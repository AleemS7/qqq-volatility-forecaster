import os
from pathlib import Path

import pandas as pd

from qqq_volatility_forecaster import config


def _delta() -> bool:
    return os.environ.get("QQQ_VOL_STORAGE", "csv") == "delta"


def _spark():
    from pyspark.sql import SparkSession

    return SparkSession.builder.getOrCreate()


def table_name(layer: str, name: str) -> str:
    schema, _, prefix = layer.partition("/")
    table = f"{prefix}_{name}" if prefix else name
    return f"{os.environ.get('QQQ_VOL_CATALOG', config.CATALOG)}.{schema}.{table}"


def table_path(layer: str, name: str, root: Path | None = None) -> Path:
    return (root or config.DATA_DIR) / layer / f"{name}.csv"


def write_table(frame: pd.DataFrame, layer: str, name: str, index: bool = True) -> str:
    frame = frame.reset_index() if index else frame
    if _delta():
        target = table_name(layer, name)
        (
            _spark()
            .createDataFrame(frame)
            .write.mode("overwrite")
            .option("overwriteSchema", "true")
            .saveAsTable(target)
        )
        return target
    path = table_path(layer, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return str(path)


def append_table(frame: pd.DataFrame, layer: str, name: str) -> str:
    if _delta():
        target = table_name(layer, name)
        _spark().createDataFrame(frame).write.mode("append").option(
            "mergeSchema", "true"
        ).saveAsTable(target)
        return target
    path = table_path(layer, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, mode="a", header=not path.exists(), index=False)
    return str(path)


def table_exists(layer: str, name: str) -> bool:
    if _delta():
        return _spark().catalog.tableExists(table_name(layer, name))
    return table_path(layer, name).exists()


def read_table(layer: str, name: str, dated: bool = True) -> pd.DataFrame:
    if not table_exists(layer, name):
        raise FileNotFoundError(f"Table {layer}/{name} not found")
    if _delta():
        frame = _spark().table(table_name(layer, name)).toPandas()
    else:
        frame = pd.read_csv(table_path(layer, name))
    if dated:
        frame["date"] = pd.to_datetime(frame["date"])
        return frame.set_index("date").sort_index()
    return frame


def upsert_table(frame: pd.DataFrame, layer: str, name: str, keys: list[str]) -> pd.DataFrame:
    if table_exists(layer, name):
        frame = pd.concat([read_table(layer, name, dated=False), frame], ignore_index=True)
    frame[keys] = frame[keys].astype(str)
    merged = frame.drop_duplicates(subset=keys, keep="last").sort_values(keys)
    write_table(merged, layer, name, index=False)
    return merged
