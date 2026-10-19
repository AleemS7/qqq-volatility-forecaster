from collections.abc import Callable
from dataclasses import dataclass, field

import pandas as pd

from qqq_volatility_forecaster.quality import rules

ISSUE_COLUMNS = ["table_name", "record_key", "rule_id", "action", "observed_value"]
ALERT_SHARE = 0.05

PRICE_QUARANTINE: dict[str, Callable[[pd.DataFrame], pd.Series]] = {
    "DQ-P01": rules.duplicate_dates,
    "DQ-P02": rules.inconsistent_range,
    "DQ-P03": rules.non_positive_price,
}
PRICE_FLAGS: dict[str, Callable[[pd.DataFrame], pd.Series]] = {
    "DQ-P04": rules.extreme_return,
    "DQ-P05": rules.calendar_gap,
}


@dataclass
class CheckResult:
    clean: pd.DataFrame
    issues: pd.DataFrame
    rows_in: int
    rows_quarantined: int
    alerts: list[str] = field(default_factory=list)


def _issues(table: str, rule_id: str, action: str, observed: pd.Series) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "table_name": table,
            "record_key": observed.index.strftime("%Y-%m-%d"),
            "rule_id": rule_id,
            "action": action,
            "observed_value": observed.astype(str).to_numpy(),
        }
    )


def _row_text(frame: pd.DataFrame) -> pd.Series:
    return pd.Series(
        [str(row) for row in frame.to_dict("records")], index=frame.index, dtype=object
    )


def _alerts(table: str, rows_in: int, rows_quarantined: int) -> list[str]:
    if rows_in and rows_quarantined / rows_in > ALERT_SHARE:
        return [f"{table}: {rows_quarantined} of {rows_in} rows quarantined"]
    return []


def check_prices(prices: pd.DataFrame, table: str = "qqq_prices") -> CheckResult:
    found = []
    bad = pd.Series(False, index=prices.index)
    for rule_id, rule in PRICE_QUARANTINE.items():
        failed = rule(prices).to_numpy()
        found.append(_issues(table, rule_id, "quarantine", _row_text(prices[failed])))
        bad |= failed
    clean = prices[~bad.to_numpy()]
    for rule_id, rule in PRICE_FLAGS.items():
        flagged = rule(clean)
        found.append(_issues(table, rule_id, "flag", clean.loc[flagged, "adj_close"]))
    quarantined = int(bad.sum())
    issues = pd.concat(found, ignore_index=True)[ISSUE_COLUMNS]
    return CheckResult(
        clean, issues, len(prices), quarantined, _alerts(table, len(prices), quarantined)
    )


def check_indices(indices: pd.DataFrame, table: str = "vol_indices") -> CheckResult:
    clean = indices.copy()
    found = []
    quarantined = 0
    for column in indices.columns:
        failed = rules.index_out_of_range(indices[column])
        found.append(_issues(table, "DQ-V01", "quarantine", indices.loc[failed, column]))
        clean.loc[failed, column] = None
        quarantined += int(failed.sum())
    issues = pd.concat(found, ignore_index=True)[ISSUE_COLUMNS]
    return CheckResult(
        clean, issues, len(indices), quarantined, _alerts(table, len(indices), quarantined)
    )
