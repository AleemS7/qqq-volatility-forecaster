# Databricks notebook source
# MAGIC %pip install -q -r ../requirements-databricks.txt

# COMMAND ----------
# MAGIC %run ./_setup

# COMMAND ----------
from qqq_volatility_forecaster.io.tables import append_table
from qqq_volatility_forecaster.ops import RunLog
from qqq_volatility_forecaster.pipeline.backtest import load_summary
from qqq_volatility_forecaster.pipeline.daily import run_daily
from qqq_volatility_forecaster.pipeline.exchange import export_tables
from qqq_volatility_forecaster.pipeline.silver import build_silver

run_log = RunLog()
try:
    silver = build_silver(run_log)
    metrics = run_daily(silver, load_summary(), run_log)
    export_tables(exports)  # noqa: F821
finally:
    append_table(run_log.frame(), "ops", "run_log")

if silver.alerts:
    raise RuntimeError("Data quality alerts: " + "; ".join(silver.alerts))
