import numpy as np
import pandas as pd

PRICE_COLUMNS = ["open", "high", "low", "close", "adj_close"]
INDEX_RANGE = (5.0, 150.0)
MAX_ABS_RETURN = 0.15
MAX_GAP_DAYS = 5
MAX_STALE_TRADING_DAYS = 2


def duplicate_dates(prices: pd.DataFrame) -> pd.Series:
    return pd.Series(prices.index.duplicated(keep="first"), index=prices.index)


def inconsistent_range(prices: pd.DataFrame) -> pd.Series:
    low, high = prices["low"], prices["high"]
    return (
        (low > prices["open"])
        | (low > prices["close"])
        | (prices["open"] > high)
        | (prices["close"] > high)
    )


def non_positive_price(prices: pd.DataFrame) -> pd.Series:
    return (prices[PRICE_COLUMNS] <= 0).any(axis=1)


def extreme_return(prices: pd.DataFrame, limit: float = MAX_ABS_RETURN) -> pd.Series:
    return prices["adj_close"].pct_change().abs() > limit


def calendar_gap(prices: pd.DataFrame, max_days: int = MAX_GAP_DAYS) -> pd.Series:
    gaps = prices.index.to_series().diff().dt.days
    return gaps > max_days


def index_out_of_range(values: pd.Series, bounds: tuple[float, float] = INDEX_RANGE) -> pd.Series:
    low, high = bounds
    return values.notna() & ((values < low) | (values > high))


def is_stale(
    last_date: pd.Timestamp, as_of: pd.Timestamp, max_days: int = MAX_STALE_TRADING_DAYS
) -> bool:
    return int(np.busday_count(last_date.date(), as_of.date())) > max_days
