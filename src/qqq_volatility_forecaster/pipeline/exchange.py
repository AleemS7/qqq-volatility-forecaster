from pathlib import Path

import pandas as pd

from qqq_volatility_forecaster.io.tables import read_table, table_exists, upsert_table, write_table
from qqq_volatility_forecaster.ops import RunLog

RAW_TABLES = ("qqq_prices", "vol_indices")
EXPORT_TABLES = (
    ("gold", "daily_metrics"),
    ("gold", "forecasts"),
    ("gold", "backtest_predictions"),
    ("gold", "daily_brief"),
)


def load_raw_files(directory: Path, run_log: RunLog) -> None:
    for name in RAW_TABLES:
        with run_log.step(f"bronze:{name}") as record:
            frame = pd.read_csv(directory / f"{name}.csv", parse_dates=["date"])
            write_table(frame, "bronze", name, index=False)
            record["rows_out"] = len(frame)


def export_tables(directory: Path) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    written = []
    for layer, name in EXPORT_TABLES:
        if table_exists(layer, name):
            path = directory / f"{name}.csv"
            read_table(layer, name, dated=False).to_csv(path, index=False)
            written.append(path)
    return written


def import_brief(directory: Path) -> int:
    path = directory / "daily_brief.csv"
    if not path.exists():
        return 0
    return len(upsert_table(pd.read_csv(path), "gold", "daily_brief", ["date"]))
