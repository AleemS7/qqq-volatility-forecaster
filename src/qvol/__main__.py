import json
import logging
import subprocess
from datetime import UTC, datetime

from qvol import config
from qvol.features.build import build_features
from qvol.io.tables import read_table, write_table
from qvol.models.evaluate import model_scores, pick_champion, summarize
from qvol.models.train import MODELS, backtest
from qvol.vrp.analysis import vrp_stats, vrp_windows

log = logging.getLogger("qvol")


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=config.ROOT, capture_output=True, text=True, check=False
    ).stdout.strip()


def main() -> None:
    prices = read_table("qqq_prices")
    indices = read_table("vol_indices")
    frame = build_features(prices, indices).loc[str(config.FIRST_TRAIN_YEAR) :]

    predictions = backtest(frame)
    scores = model_scores(predictions)
    summary = summarize(scores)
    champion = pick_champion(summary)
    windows = vrp_windows(frame)

    write_table(predictions.set_index("date"), "predictions", config.RESULTS_DIR)
    scores.to_csv(config.RESULTS_DIR / "model_scores.csv", index=False, float_format="%.4f")
    write_table(windows, "vrp_windows", config.RESULTS_DIR)

    report = {
        "commit": _git("rev-parse", "HEAD"),
        "dirty": bool(_git("status", "--porcelain", "--", "src")),
        "run_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "data": {
            "price_start": str(prices.index.min().date()),
            "price_end": str(prices.index.max().date()),
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
    (config.RESULTS_DIR / "summary.json").write_text(json.dumps(report, indent=2) + "\n")

    log.info("Commit %s%s", report["commit"][:8], " (dirty)" if report["dirty"] else "")
    log.info("\n%s", summary.round(3).to_string())
    log.info("Champion: %s", champion)
    log.info("VRP: %s", json.dumps(report["vrp"], indent=2))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format=config.LOG_FORMAT)
    main()
