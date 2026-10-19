import numpy as np
import pandas as pd
import pytest

from qqq_volatility_forecaster.config import VIX_SERIES, VXN_SERIES


def synthetic_market(days: int, seed: int = 0) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2000-01-03", periods=days, name="date")
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.015, days)))
    prices = pd.DataFrame(
        {
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "adj_close": close,
            "volume": 1_000_000,
        },
        index=dates,
    )
    indices = pd.DataFrame(
        {VXN_SERIES: rng.uniform(15, 40, days), VIX_SERIES: rng.uniform(12, 35, days)},
        index=dates,
    )
    return prices, indices


@pytest.fixture
def market() -> tuple[pd.DataFrame, pd.DataFrame]:
    return synthetic_market(400)
