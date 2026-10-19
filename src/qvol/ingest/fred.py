from io import StringIO

import pandas as pd
import requests

FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"


def fetch_series(series_id: str) -> pd.Series:
    response = requests.get(FRED_CSV_URL, params={"id": series_id}, timeout=30)
    response.raise_for_status()
    frame = pd.read_csv(StringIO(response.text), na_values=".")
    series = pd.Series(
        pd.to_numeric(frame.iloc[:, 1], errors="coerce").to_numpy(),
        index=pd.DatetimeIndex(pd.to_datetime(frame.iloc[:, 0]), name="date"),
        name=series_id,
    )
    return series.sort_index()
