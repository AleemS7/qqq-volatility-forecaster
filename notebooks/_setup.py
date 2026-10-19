# Databricks notebook source
import os
import sys
from pathlib import Path

dbutils.widgets.text("catalog", "qqq_volatility_forecaster_dv")  # noqa: F821
catalog = dbutils.widgets.get("catalog")  # noqa: F821

os.environ["QQQ_VOL_STORAGE"] = "delta"
os.environ["QQQ_VOL_CATALOG"] = catalog
sys.path.insert(0, str(Path.cwd().parent / "src"))

volume = Path(f"/Volumes/{catalog}/bronze/raw")
exports = Path(f"/Volumes/{catalog}/gold/exports")
