from pathlib import Path

import pandas as pd

from qqq_volatility_forecaster import config


def table_path(layer: str, name: str, root: Path | None = None) -> Path:
    return (root or config.DATA_DIR) / layer / f"{name}.csv"


def write_table(frame: pd.DataFrame, layer: str, name: str, index: bool = True) -> Path:
    path = table_path(layer, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=index)
    return path


def append_table(frame: pd.DataFrame, layer: str, name: str) -> Path:
    path = table_path(layer, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, mode="a", header=not path.exists(), index=False)
    return path


def upsert_table(frame: pd.DataFrame, layer: str, name: str, keys: list[str]) -> pd.DataFrame:
    if table_exists(layer, name):
        frame = pd.concat([read_table(layer, name, dated=False), frame], ignore_index=True)
    merged = frame.drop_duplicates(subset=keys, keep="last").sort_values(keys)
    write_table(merged, layer, name, index=False)
    return merged


def read_table(layer: str, name: str, dated: bool = True) -> pd.DataFrame:
    path = table_path(layer, name)
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")
    if dated:
        return pd.read_csv(path, index_col="date", parse_dates=["date"])
    return pd.read_csv(path)


def table_exists(layer: str, name: str) -> bool:
    return table_path(layer, name).exists()
