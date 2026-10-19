import argparse
import json
import logging

from qqq_volatility_forecaster import config
from qqq_volatility_forecaster.brief.evaluate import (
    EVAL_PATH,
    build_eval_set,
    run_eval,
    write_eval_set,
)
from qqq_volatility_forecaster.brief.llm_client import default_llm
from qqq_volatility_forecaster.ingest.run import ingest
from qqq_volatility_forecaster.io.tables import append_table, read_table
from qqq_volatility_forecaster.ops import RunLog
from qqq_volatility_forecaster.pipeline.backtest import load_summary, run_backtest
from qqq_volatility_forecaster.pipeline.brief import run_brief
from qqq_volatility_forecaster.pipeline.daily import run_daily
from qqq_volatility_forecaster.pipeline.silver import build_silver
from qqq_volatility_forecaster.pipeline.site import run_site

log = logging.getLogger("qqq_volatility_forecaster")


def _backtest(run_log: RunLog) -> None:
    silver = build_silver(run_log)
    run_backtest(silver.prices, silver.indices, run_log)


def _daily(run_log: RunLog) -> None:
    ingest(run_log)
    run_daily(build_silver(run_log), load_summary(), run_log)


def _brief_eval_set(run_log: RunLog) -> None:
    cases = build_eval_set(
        read_table("gold", "backtest_predictions", dated=False),
        read_table("gold", "features_daily"),
        load_summary(),
    )
    write_eval_set(cases)
    log.info("Wrote %d eval cases to %s", len(cases), EVAL_PATH)


def _brief_eval(run_log: RunLog) -> None:
    report = run_eval(default_llm())
    (config.RESULTS_DIR / "brief_eval.json").write_text(json.dumps(report, indent=2) + "\n")
    log.info(
        "Brief eval: %d/%d verified, passed=%s",
        report["verified"],
        report["cases"],
        report["passed"],
    )


COMMANDS = {
    "brief-eval-set": _brief_eval_set,
    "brief-eval": _brief_eval,
    "ingest": ingest,
    "backtest": _backtest,
    "daily": _daily,
    "brief": run_brief,
    "site": run_site,
}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="qqq-volatility-forecaster")
    parser.add_argument("command", choices=sorted(COMMANDS))
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format=config.LOG_FORMAT)
    run_log = RunLog()
    try:
        COMMANDS[args.command](run_log)
    finally:
        append_table(run_log.frame(), "ops", "run_log")
