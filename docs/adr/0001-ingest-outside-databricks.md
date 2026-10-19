# 0001: Ingest runs in GitHub Actions, not Databricks

- **Status:** Accepted, 2026-10-18
- **Context:** Databricks Free Edition limits outbound internet access to trusted domains, so Yahoo, FRED, and the Anthropic API may be unreachable from jobs.
- **Decision:** GitHub Actions downloads the raw files and uploads them to a Unity Catalog volume, then triggers the bundle job. The brief also runs in GitHub Actions, using CSV exports in a second volume.
- **Consequences:** Two systems to monitor. The volume is the only exchange point, so each side is testable alone. Deviates from Southern's Data Factory or Logic Apps ingest standard.
