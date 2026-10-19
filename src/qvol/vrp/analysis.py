import pandas as pd

from qvol.config import HORIZON
from qvol.features.build import TARGET


def vrp_windows(frame: pd.DataFrame, horizon: int = HORIZON) -> pd.DataFrame:
    windows = frame.iloc[::horizon][["vxn", TARGET]].dropna()
    windows = windows.rename(columns={"vxn": "implied", TARGET: "realized"})
    windows["premium"] = windows["implied"] - windows["realized"]
    windows["scoreboard"] = windows["premium"].cumsum()
    return windows


def vrp_stats(windows: pd.DataFrame) -> dict:
    premium = windows["premium"]
    typical_gain = premium[premium > 0].median()
    worst_date = premium.idxmin()
    scoreboard = windows["scoreboard"]
    drawdown = scoreboard - scoreboard.cummax()
    return {
        "windows": int(len(windows)),
        "start": str(windows.index.min().date()),
        "end": str(windows.index.max().date()),
        "share_overpriced": float((premium > 0).mean()),
        "median_premium": float(premium.median()),
        "mean_premium": float(premium.mean()),
        "typical_gain": float(typical_gain),
        "worst_premium": float(premium.min()),
        "worst_window_start": str(worst_date.date()),
        "worst_window_months_erased": float(-premium.min() / typical_gain),
        "max_scoreboard_drawdown": float(-drawdown.min()),
        "max_drawdown_months_erased": float(-drawdown.min() / typical_gain),
    }
