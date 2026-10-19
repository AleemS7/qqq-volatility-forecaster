import pandas as pd
import pytest

from qqq_volatility_forecaster.quality import rules
from qqq_volatility_forecaster.quality.quarantine import check_indices, check_prices


def _prices(rows: list[tuple], dates: list[str] | None = None) -> pd.DataFrame:
    dates = dates or [str(d.date()) for d in pd.bdate_range("2024-01-01", periods=len(rows))]
    frame = pd.DataFrame(rows, columns=["open", "high", "low", "close"], dtype=float)
    frame["adj_close"] = frame["close"]
    frame["volume"] = 100
    frame.index = pd.DatetimeIndex(dates, name="date")
    return frame


def test_duplicate_dates_keeps_first():
    prices = _prices([(1, 2, 1, 2)] * 3, ["2024-01-02", "2024-01-02", "2024-01-03"])
    assert rules.duplicate_dates(prices).tolist() == [False, True, False]


@pytest.mark.parametrize(
    ("row", "bad"),
    [
        ((10, 11, 9, 10), False),
        ((10, 10, 10, 10), False),
        ((9, 11, 9, 11), False),
        ((8.99, 11, 9, 10), True),
        ((10, 11, 9, 11.01), True),
        ((10, 9, 11, 10), True),
    ],
)
def test_inconsistent_range_boundaries(row, bad):
    assert rules.inconsistent_range(_prices([row])).iloc[0] == bad


@pytest.mark.parametrize(("price", "bad"), [(0.01, False), (0.0, True), (-1.0, True)])
def test_non_positive_price(price, bad):
    assert rules.non_positive_price(_prices([(price, 1, price, 1)])).iloc[0] == bad


def test_extreme_return_boundary():
    prices = _prices([(1, 1, 1, 100), (1, 1, 1, 114.9), (1, 1, 1, 97.6)])
    assert rules.extreme_return(prices).tolist() == [False, False, True]


def test_calendar_gap_boundary():
    prices = _prices([(1, 1, 1, 1)] * 3, ["2024-01-01", "2024-01-06", "2024-01-12"])
    assert rules.calendar_gap(prices).tolist() == [False, False, True]


@pytest.mark.parametrize(
    ("value", "bad"), [(5.0, False), (150.0, False), (4.99, True), (150.01, True)]
)
def test_index_range_boundaries(value, bad):
    assert rules.index_out_of_range(pd.Series([value])).iloc[0] == bad


def test_missing_index_value_is_not_quarantined():
    assert not rules.index_out_of_range(pd.Series([float("nan")])).iloc[0]


@pytest.mark.parametrize(("as_of", "stale"), [("2024-01-10", False), ("2024-01-11", True)])
def test_is_stale(as_of, stale):
    assert rules.is_stale(pd.Timestamp("2024-01-08"), pd.Timestamp(as_of)) == stale


def test_bad_price_row_lands_in_quarantine():
    prices = _prices([(10, 11, 9, 10), (10, 11, 12, 10), (10, 11, 9, 10)])
    result = check_prices(prices)
    assert len(result.clean) == 2
    assert result.rows_quarantined == 1
    quarantined = result.issues[result.issues["action"] == "quarantine"]
    assert quarantined["rule_id"].tolist() == ["DQ-P02"]
    assert quarantined["record_key"].tolist() == [str(prices.index[1].date())]
    assert result.alerts


def test_extreme_return_is_flagged_not_dropped():
    prices = _prices([(100, 100, 100, 100), (50, 50, 50, 50)])
    result = check_prices(prices)
    assert len(result.clean) == 2
    assert result.issues["rule_id"].tolist() == ["DQ-P04"]
    assert result.issues["action"].tolist() == ["flag"]


def test_out_of_range_index_value_is_nulled():
    indices = pd.DataFrame(
        {"VXNCLS": [20.0, 200.0, None], "VIXCLS": [15.0, 16.0, 17.0]},
        index=pd.bdate_range("2024-01-01", periods=3, name="date"),
    )
    result = check_indices(indices)
    assert result.clean["VXNCLS"].isna().tolist() == [False, True, True]
    assert result.rows_quarantined == 1
    assert result.issues["rule_id"].tolist() == ["DQ-V01"]
