# 0007: One table module with CSV and Delta backends

- **Status:** Accepted, 2026-10-18
- **Context:** The same logic must run locally, in tests, and in Databricks. Southern's standard keeps business logic separate from data access.
- **Decision:** `io/tables.py` is the only module that reads or writes tables. `QQQ_VOL_STORAGE=delta` switches it from local CSV to Unity Catalog Delta tables.
- **Consequences:** Notebooks stay thin. The full pipeline is tested end to end on CSV. The Delta path is exercised only in Databricks.
