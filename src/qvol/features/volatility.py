import numpy as np
import pandas as pd

from qvol.config import HORIZON, TRADING_DAYS


def log_returns(adj_close: pd.Series) -> pd.Series:
    return np.log(adj_close / adj_close.shift(1))


def realized_vol(returns: pd.Series, window: int) -> pd.Series:
    return 100 * np.sqrt(TRADING_DAYS / window * returns.pow(2).rolling(window).sum())


def forward_realized_vol(returns: pd.Series, horizon: int = HORIZON) -> pd.Series:
    return realized_vol(returns, horizon).shift(-horizon)
