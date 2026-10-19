# Databricks notebook source
# MAGIC %pip install -q -r ../requirements-databricks.txt

# COMMAND ----------
# MAGIC %run ./_setup

# COMMAND ----------
from qqq_volatility_forecaster.io.tables import append_table
from qqq_volatility_forecaster.ops import RunLog
from qqq_volatility_forecaster.pipeline.exchange import import_brief, load_raw_files

run_log = RunLog()
load_raw_files(volume, run_log)  # noqa: F821
import_brief(exports)  # noqa: F821
append_table(run_log.frame(), "ops", "run_log")
dbutils.jobs.taskValues.set("run_id", run_log.run_id)  # noqa: F821
