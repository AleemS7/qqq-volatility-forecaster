# 0004: Managed Delta tables instead of external tables

- **Status:** Accepted, 2026-10-18
- **Context:** Southern's Databricks standard prefers external tables. Free Edition has no external storage.
- **Decision:** Use managed tables in the `qqq_volatility_forecaster_dv` and `qqq_volatility_forecaster_pr` catalogs.
- **Consequences:** Simpler setup. Moving to an Azure workspace later means re-creating the tables as external tables.
