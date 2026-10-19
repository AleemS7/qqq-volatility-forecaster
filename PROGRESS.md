# Progress

## 2026-10-18

Built on `feature/1-core-backtest` :

- **Core:** ingest, target, features, walk-forward M0–M4, champion rule, overpricing analysis. Results in the README from commit `c92fc26`.
- **Pipeline:** data quality rules and quarantine, retries, stale detection, run log, daily scoring, CSV and Delta storage, Databricks bundle and notebooks, daily GitHub Actions workflows.
- **Brief:** LangGraph workflow, number verifier, fallback template, 20-day eval set.
- **Page:** static GitHub Pages "today" page with a stale-data banner.
- **Quality:** 85 tests, 84% coverage, ruff, pre-commit, pip-audit, CodeQL, Dependabot.

Not done yet:

- Create the GitHub repo, push `main`, `develop`, and this branch, and open the PR.
- Databricks: create the workspace and catalogs, `bundle deploy -t dv`, first run (runbook section "First-time setup"). The Delta path has not run against a real workspace.
- Brief eval against the real model (`qqq-volatility-forecaster brief-eval`). Needs `ANTHROPIC_API_KEY`.
- Power BI `.pbip` with the four pages. Needs Power BI Desktop.
