import json
from pathlib import Path

import numpy as np
import pandas as pd

from qqq_volatility_forecaster import config
from qqq_volatility_forecaster.brief.graph import build_graph
from qqq_volatility_forecaster.brief.llm_client import LlmClient

EVAL_PATH = config.ROOT / "tests" / "fixtures" / "brief_eval.json"
TARGET_SHARE = 0.95


def build_eval_set(
    predictions: pd.DataFrame, features: pd.DataFrame, summary: dict, days: int = 20
) -> list[dict]:
    champion = summary["champion"]
    rows = predictions[predictions["model"] == champion].reset_index(drop=True)
    picks = rows.iloc[np.linspace(0, len(rows) - 1, days).astype(int)]
    cases = []
    for _, row in picks.iterrows():
        feature = features.loc[pd.Timestamp(row["date"])]
        cases.append(
            {
                "status": "ok",
                "date": str(pd.Timestamp(row["date"]).date()),
                "forecast": round(float(row["forecast"]), 2),
                "vxn": round(float(row["vxn"]), 2),
                "vix": round(float(feature["vix"]), 2),
                "rv_21": round(float(feature["rv_21"]), 2),
                "premium": round(float(row["vxn"] - row["forecast"]), 2),
                "backtest_mae": summary["models"][champion]["mae"],
                "share_overpriced": summary["vrp"]["share_overpriced"],
            }
        )
    return cases


def write_eval_set(cases: list[dict], path: Path = EVAL_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cases, indent=2) + "\n")


def run_eval(llm: LlmClient, path: Path = EVAL_PATH) -> dict:
    cases = json.loads(path.read_text())
    results = []
    for case in cases:
        state = build_graph(llm, lambda case=case: case).invoke({})
        results.append(
            {
                "date": case["date"],
                "status": state["status"],
                "attempts": state["attempts"],
                "errors": state["errors"],
            }
        )
    verified = sum(r["status"] == "llm_verified" for r in results)
    share = verified / len(results)
    return {
        "model": llm.model_id,
        "prompt_version": config.BRIEF_PROMPT_VERSION,
        "cases": len(results),
        "verified": verified,
        "share": share,
        "passed": share >= TARGET_SHARE,
        "results": results,
    }
