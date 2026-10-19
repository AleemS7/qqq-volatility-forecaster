import pandas as pd
import yfinance as yf

COLUMNS = {
    "Open": "open",
    "High": "high",
    "Low": "low",
    "Close": "close",
    "Adj Close": "adj_close",
    "Volume": "volume",
}


def fetch_prices(ticker: str, start: str) -> pd.DataFrame:
    raw = yf.download(ticker, start=start, auto_adjust=False, actions=False, progress=False)
    if raw.empty:
        raise RuntimeError(f"No price data returned for {ticker}")
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    prices = raw.rename(columns=COLUMNS)[list(COLUMNS.values())]
    prices.index = pd.DatetimeIndex(raw.index).tz_localize(None).normalize()
    prices.index.name = "date"
    return prices.sort_index()
