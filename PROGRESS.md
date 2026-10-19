# Progress

## 2026-10-18

Built on `feature/1-core-backtest`:

- **Core:** ingest, target, features, walk-forward M0–M4, champion rule, overpricing analysis. Results in the README from commit `c92fc26`.
- **Pipeline:** data quality rules and quarantine, retries, stale detection, run log, daily scoring, CSV and Delta storage, Databricks bundle and notebooks, daily GitHub Actions workflows.
- **Brief:** LangGraph workflow, number verifier, fallback template, 20-day eval set.
- **Page:** static GitHub Pages "today" page with a stale-data banner.
- **Dashboard:** Databricks dashboard with four pages, deployed to `dv`. Replaces Power BI (ADR 0009).
- **Quality:** 86 tests, 84% coverage, ruff, pre-commit, pip-audit, CodeQL, Dependabot.

Not done yet:

- Databricks `dv` is deployed and both jobs ran successfully on 2026-10-18. Five days in a row with no manual steps is still needed.
- GitHub secrets for the daily workflows.
- Brief eval against the real model (`qqq-volatility-forecaster brief-eval`). Needs `ANTHROPIC_API_KEY`.
