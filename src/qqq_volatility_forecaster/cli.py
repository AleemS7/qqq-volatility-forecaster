import argparse
import logging

from qqq_volatility_forecaster import config
from qqq_volatility_forecaster.ingest.run import ingest
from qqq_volatility_forecaster.io.tables import append_table
from qqq_volatility_forecaster.ops import RunLog
from qqq_volatility_forecaster.pipeline.backtest import load_summary, run_backtest
from qqq_volatility_forecaster.pipeline.daily import run_daily
from qqq_volatility_forecaster.pipeline.silver import build_silver

log = logging.getLogger("qqq_volatility_forecaster")


def _backtest(run_log: RunLog) -> None:
    silver = build_silver(run_log)
    run_backtest(silver.prices, silver.indices, run_log)


def _daily(run_log: RunLog) -> None:
    ingest(run_log)
    run_daily(build_silver(run_log), load_summary(), run_log)


COMMANDS = {
    "ingest": ingest,
    "backtest": _backtest,
    "daily": _daily,
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
