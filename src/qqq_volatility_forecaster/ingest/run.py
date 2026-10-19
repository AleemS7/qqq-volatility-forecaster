import logging

import pandas as pd

from qqq_volatility_forecaster import config
from qqq_volatility_forecaster.ingest.fred import fetch_series
from qqq_volatility_forecaster.ingest.retry import with_retries
from qqq_volatility_forecaster.ingest.yahoo import fetch_prices
from qqq_volatility_forecaster.io.tables import write_table
from qqq_volatility_forecaster.ops import RunLog

log = logging.getLogger(__name__)


def _fetch_prices() -> pd.DataFrame:
    return with_retries(fetch_prices)(config.TICKER, config.PRICE_START)


def _fetch_indices() -> pd.DataFrame:
    series = [with_retries(fetch_series)(s) for s in (config.VXN_SERIES, config.VIX_SERIES)]
    return pd.concat(series, axis=1, sort=True)


SOURCES = {"qqq_prices": _fetch_prices, "vol_indices": _fetch_indices}


def ingest(run_log: RunLog | None = None) -> RunLog:
    run_log = run_log or RunLog()
    for name, fetch in SOURCES.items():
        with run_log.step(f"ingest:{name}") as record:
            try:
                frame = fetch()
            except Exception:
                log.exception("Source %s failed after retries, marking stale", name)
                record["status"] = "stale"
                continue
            write_table(frame, "bronze", name)
            record["rows_out"] = len(frame)
            log.info("Ingested %s: %d rows through %s", name, len(frame), frame.index.max().date())
    return run_log
