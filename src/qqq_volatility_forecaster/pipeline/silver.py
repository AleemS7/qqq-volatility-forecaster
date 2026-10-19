import logging
from dataclasses import dataclass

import pandas as pd

from qqq_volatility_forecaster.io.tables import append_table, read_table, write_table
from qqq_volatility_forecaster.ops import RunLog
from qqq_volatility_forecaster.quality.quarantine import CheckResult, check_indices, check_prices
from qqq_volatility_forecaster.quality.rules import is_stale

log = logging.getLogger(__name__)


@dataclass
class Silver:
    prices: pd.DataFrame
    indices: pd.DataFrame
    alerts: list[str]
    stale: list[str]


def _record(record: dict, result: CheckResult) -> None:
    record["rows_in"] = result.rows_in
    record["rows_out"] = len(result.clean)
    record["rows_quarantined"] = result.rows_quarantined


def build_silver(run_log: RunLog, as_of: pd.Timestamp | None = None) -> Silver:
    as_of = as_of or pd.Timestamp.today().normalize()
    alerts: list[str] = []
    stale: list[str] = []
    checks = {"qqq_prices": check_prices, "vol_indices": check_indices}
    clean = {}
    for name, check in checks.items():
        with run_log.step(f"silver:{name}") as record:
            result = check(read_table("bronze", name))
            _record(record, result)
            if not result.issues.empty:
                append_table(result.issues.assign(run_id=run_log.run_id), "ops", "quarantine")
            write_table(result.clean, "silver", name)
            alerts += result.alerts
            last = result.clean.dropna(how="all").index.max()
            if is_stale(last, as_of):
                stale.append(name)
                alerts.append(f"{name}: stale, last row {last.date()}")
            clean[name] = result.clean
    for alert in alerts:
        log.warning("ALERT %s", alert)
    return Silver(clean["qqq_prices"], clean["vol_indices"], alerts, stale)
