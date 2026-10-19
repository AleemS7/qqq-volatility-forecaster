# Databricks notebook source
# MAGIC %pip install -q -r ../requirements-databricks.txt

# COMMAND ----------
# MAGIC %run ./_setup

# COMMAND ----------
import mlflow

from qqq_volatility_forecaster.io.tables import append_table
from qqq_volatility_forecaster.ops import RunLog
from qqq_volatility_forecaster.pipeline.backtest import SUMMARY_PATH, run_backtest
from qqq_volatility_forecaster.pipeline.silver import build_silver

run_log = RunLog()
mlflow.set_experiment(f"/Shared/{catalog}")  # noqa: F821
with mlflow.start_run(run_name=run_log.run_id):
    silver = build_silver(run_log)
    report = run_backtest(silver.prices, silver.indices, run_log)
    mlflow.set_tags({"commit": report["commit"], "champion": report["champion"]})
    mlflow.log_param("data_fingerprint", report["data"]["fingerprint"])
    for model_id, scores in report["models"].items():
        mlflow.log_metric(f"{model_id}_mae", scores["mae"])
        mlflow.log_metric(f"{model_id}_beat_share", scores["beat_share"])
    mlflow.log_artifact(str(SUMMARY_PATH))
append_table(run_log.frame(), "ops", "run_log")
