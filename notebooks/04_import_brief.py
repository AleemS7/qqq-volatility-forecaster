# Databricks notebook source
# MAGIC %run ./_setup

# COMMAND ----------
from qqq_volatility_forecaster.pipeline.exchange import import_brief

print(f"daily_brief rows: {import_brief(exports)}")  # noqa: F821
