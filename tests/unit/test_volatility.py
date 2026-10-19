import math

import numpy as np
import pandas as pd
import pytest

from qqq_volatility_forecaster.features.volatility import (
    forward_realized_vol,
    log_returns,
    realized_vol,
)


def test_log_returns():
    returns = log_returns(pd.Series([100.0, 110.0, 99.0]))
    assert math.isnan(returns.iloc[0])
    assert returns.iloc[1] == pytest.approx(math.log(1.1))
    assert returns.iloc[2] == pytest.approx(math.log(0.9))


def test_realized_vol_matches_hand_computation():
    returns = pd.Series([0.01, -0.02, 0.03])
    expected = 100 * math.sqrt(252 / 3 * (0.0001 + 0.0004 + 0.0009))
    rv = realized_vol(returns, 3)
    assert rv.iloc[:2].isna().all()
    assert rv.iloc[2] == pytest.approx(expected)
    assert expected == pytest.approx(34.2929, abs=1e-4)


def test_forward_target_uses_next_days_only():
    returns = pd.Series([0.05, 0.01, -0.02, 0.03, 0.04])
    target = forward_realized_vol(returns, horizon=2)
    assert target.iloc[0] == pytest.approx(100 * math.sqrt(126 * (0.01**2 + 0.02**2)))
    assert target.iloc[2] == pytest.approx(100 * math.sqrt(126 * (0.03**2 + 0.04**2)))
    assert target.iloc[-2:].isna().all()


def test_forward_target_ignores_today():
    returns = pd.Series([0.0, 0.01, 0.01, 0.0])
    shocked = returns.copy()
    shocked.iloc[0] = 0.5
    np.testing.assert_allclose(
        forward_realized_vol(returns, 2).iloc[0], forward_realized_vol(shocked, 2).iloc[0]
    )
