from pathlib import Path

import pandas as pd

from qqq_volatility_forecaster import config


def _path(name: str, directory: Path) -> Path:
    return directory / f"{name}.csv"


def write_table(frame: pd.DataFrame, name: str, directory: Path = config.DATA_DIR) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = _path(name, directory)
    frame.to_csv(path)
    return path


def read_table(name: str, directory: Path = config.DATA_DIR) -> pd.DataFrame:
    path = _path(name, directory)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run `python -m qqq_volatility_forecaster.ingest` first."
        )
    return pd.read_csv(path, index_col="date", parse_dates=["date"])
