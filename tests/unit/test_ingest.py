import numpy as np
import pandas as pd
import pytest

from qqq_volatility_forecaster.ingest import fred, yahoo


class FakeResponse:
    text = "observation_date,VXNCLS\n2024-01-02,18.5\n2024-01-01,.\n2024-01-03,19.25\n"

    def raise_for_status(self) -> None:
        pass


def test_fred_parses_holidays_as_null(monkeypatch):
    monkeypatch.setattr(fred.requests, "get", lambda *a, **k: FakeResponse())
    series = fred.fetch_series("VXNCLS")
    assert series.name == "VXNCLS"
    assert series.index.is_monotonic_increasing
    assert np.isnan(series.loc["2024-01-01"])
    assert series.loc["2024-01-03"] == 19.25


def test_yahoo_flattens_columns_and_rounds(monkeypatch):
    dates = pd.DatetimeIndex(["2024-01-03", "2024-01-02"], tz="America/New_York")
    columns = pd.MultiIndex.from_product(
        [["Adj Close", "Close", "High", "Low", "Open", "Volume"], ["QQQ"]]
    )
    raw = pd.DataFrame(np.full((2, 6), 100.123456), index=dates, columns=columns)
    monkeypatch.setattr(yahoo.yf, "download", lambda *a, **k: raw)
    prices = yahoo.fetch_prices("QQQ", "2024-01-01")
    assert list(prices.columns) == ["open", "high", "low", "close", "adj_close", "volume"]
    assert prices.index.tz is None
    assert prices.index.is_monotonic_increasing
    assert prices["adj_close"].iloc[0] == 100.1235


def test_yahoo_empty_response_raises(monkeypatch):
    monkeypatch.setattr(yahoo.yf, "download", lambda *a, **k: pd.DataFrame())
    with pytest.raises(RuntimeError):
        yahoo.fetch_prices("QQQ", "2024-01-01")
