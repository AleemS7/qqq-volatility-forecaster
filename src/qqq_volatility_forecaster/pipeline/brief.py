import logging
from datetime import UTC, datetime

import pandas as pd

from qqq_volatility_forecaster.brief.graph import LABEL, build_graph
from qqq_volatility_forecaster.brief.llm_client import LlmClient, default_llm
from qqq_volatility_forecaster.io.tables import read_table, upsert_table
from qqq_volatility_forecaster.ops import RunLog

log = logging.getLogger(__name__)


def latest_metrics() -> dict:
    metrics = read_table("gold", "daily_metrics", dated=False).sort_values("date").iloc[-1]
    return {k: (v.item() if hasattr(v, "item") else v) for k, v in metrics.dropna().items()}


def run_brief(run_log: RunLog, llm: LlmClient | None = None) -> dict:
    llm = llm or default_llm()
    with run_log.step("gold:brief") as record:
        state = build_graph(llm, latest_metrics).invoke({})
        brief = {
            "date": state["metrics"]["date"],
            "text": state["draft"],
            "label": LABEL if state["status"] == "llm_verified" else "Template summary.",
            "status": state["status"],
            "model": state["model_id"],
            "prompt_version": state["prompt_version"],
            "attempts": state["attempts"],
            "errors": "; ".join(state["errors"]),
            "run_id": run_log.run_id,
            "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        }
        upsert_table(pd.DataFrame([brief]), "gold", "daily_brief", ["date"])
        record["rows_out"] = 1
    log.info("Brief %s (%s, %d attempts)", brief["status"], brief["date"], brief["attempts"])
    return brief
