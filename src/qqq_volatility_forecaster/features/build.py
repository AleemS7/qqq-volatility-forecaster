import pandas as pd

from qqq_volatility_forecaster.config import HORIZON, VIX_SERIES, VXN_SERIES
from qqq_volatility_forecaster.features.volatility import (
    forward_realized_vol,
    log_returns,
    realized_vol,
)

FEATURES = ["rv_5", "rv_21", "rv_63", "vxn", "vix", "vxn_minus_rv21", "ret_21", "drawdown_252"]
TARGET = "y"


def build_features(prices: pd.DataFrame, indices: pd.DataFrame) -> pd.DataFrame:
    close = prices["adj_close"]
    returns = log_returns(close)
    frame = pd.DataFrame(index=prices.index)
    frame["rv_5"] = realized_vol(returns, 5)
    frame["rv_21"] = realized_vol(returns, 21)
    frame["rv_63"] = realized_vol(returns, 63)
    frame["vxn"] = indices[VXN_SERIES].reindex(prices.index)
    frame["vix"] = indices[VIX_SERIES].reindex(prices.index)
    frame["vxn_minus_rv21"] = frame["vxn"] - frame["rv_21"]
    frame["ret_21"] = 100 * (close / close.shift(21) - 1)
    frame["drawdown_252"] = 100 * (close / close.rolling(252).max() - 1)
    frame[TARGET] = forward_realized_vol(returns, HORIZON)
    return frame
