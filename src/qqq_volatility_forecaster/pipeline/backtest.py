import hashlib
import json
import logging
import subprocess
from datetime import UTC, datetime

import pandas as pd

from qqq_volatility_forecaster import config
from qqq_volatility_forecaster.features.build import build_features
from qqq_volatility_forecaster.io.tables import write_table
from qqq_volatility_forecaster.models.evaluate import model_scores, pick_champion, summarize
from qqq_volatility_forecaster.models.train import MODELS, backtest
from qqq_volatility_forecaster.ops import RunLog
from qqq_volatility_forecaster.vrp.analysis import vrp_stats, vrp_windows

log = logging.getLogger(__name__)

SUMMARY_PATH = config.RESULTS_DIR / "summary.json"


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=config.ROOT, capture_output=True, text=True, check=False
    ).stdout.strip()


def data_fingerprint(*frames: pd.DataFrame) -> str:
    digest = hashlib.sha256()
    for frame in frames:
        digest.update(pd.util.hash_pandas_object(frame, index=True).to_numpy().tobytes())
    return digest.hexdigest()[:16]


def run_backtest(prices: pd.DataFrame, indices: pd.DataFrame, run_log: RunLog) -> dict:
    with run_log.step("gold:backtest") as record:
        frame = build_features(prices, indices).loc[str(config.FIRST_TRAIN_YEAR) :]
        predictions = backtest(frame)
        scores = model_scores(predictions)
        summary = summarize(scores)
        champion = pick_champion(summary)
        windows = vrp_windows(frame)
        record["rows_in"] = len(frame)
        record["rows_out"] = len(predictions)

    write_table(predictions, "gold", "backtest_predictions", index=False)
    write_table(scores, "gold", "model_scores", index=False)
    write_table(windows, "gold", "vrp_windows")
    config.RESULTS_DIR.mkdir(exist_ok=True)
    scores.to_csv(config.RESULTS_DIR / "model_scores.csv", index=False, float_format="%.4f")

    report = {
        "commit": _git("rev-parse", "HEAD"),
        "dirty": bool(_git("status", "--porcelain", "--", "src")),
        "run_id": run_log.run_id,
        "run_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "data": {
            "price_start": str(prices.index.min().date()),
            "price_end": str(prices.index.max().date()),
            "fingerprint": data_fingerprint(prices, indices),
            "test_years": sorted(int(y) for y in predictions["year"].unique()),
            "test_rows": int((predictions["model"] == "M0").sum()),
        },
        "models": {
            model_id: {"name": MODELS[model_id].name, **row}
            for model_id, row in summary.round(4).to_dict(orient="index").items()
        },
        "champion": champion,
        "vrp": vrp_stats(windows),
    }
    SUMMARY_PATH.write_text(json.dumps(report, indent=2) + "\n")
    log.info("Commit %s%s", report["commit"][:8], " (dirty)" if report["dirty"] else "")
    log.info("\n%s", summary.round(3).to_string())
    log.info("Champion: %s", champion)
    return report


def load_summary() -> dict:
    if not SUMMARY_PATH.exists():
        raise FileNotFoundError(f"{SUMMARY_PATH} not found. Run the backtest first.")
    return json.loads(SUMMARY_PATH.read_text())
