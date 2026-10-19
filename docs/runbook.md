# Runbook

## Commands

```bash
qqq-volatility-forecaster ingest       # download QQQ, VXN, VIX into bronze
qqq-volatility-forecaster backtest     # quality checks, walk-forward backtest, results/summary.json
qqq-volatility-forecaster daily        # ingest, quality checks, score today with the champion
qqq-volatility-forecaster brief        # LangGraph summary with number checks, or the template
qqq-volatility-forecaster site         # render site/index.html
qqq-volatility-forecaster brief-eval   # run the 20-day brief evaluation (needs ANTHROPIC_API_KEY)
```

Every command appends to `ops.run_log` with a `run_id`.

## Schedule

| Workflow | When (UTC) | Does |
|---|---|---|
| `ingest-daily` | 22:30 weekdays | Downloads, uploads to `/Volumes/<catalog>/bronze/raw`, runs the daily Databricks job |
| `brief-daily` | After `ingest-daily` succeeds | Pulls `daily_metrics`, writes the brief, imports it into `gold.daily_brief` |
| `pages-daily` | After `brief-daily` succeeds | Rebuilds and deploys the public page |
| `ci-weekly` | Sunday 12:00 | Lint, tests, `pip-audit` |
| `deploy` | Push to `main` | `databricks bundle deploy -t pr` |

## Dashboard

`QQQ Volatility Forecaster (<target>)` in Databricks, deployed with the bundle from `dashboards/qqq_volatility_forecaster.lvdash.json`. Pages: forecast vs. actual, overpricing history, model scorecard, pipeline health.

## Alerts

### Job failed

- **Check:** the failed task in the Databricks job run, then `ops.run_log` for that `run_id`.
- **Fix:** the failing step. Most failures are a source outage or a schema change in the download.
- **Replay:** `gh workflow run ingest-daily`, or `databricks bundle run qqq_volatility_forecaster_daily -t pr`.

### Quarantine spike (more than 5% of a day's rows)

- **Check:** `SELECT rule_id, count(*) FROM ops.quarantine WHERE run_id = '<run_id>' GROUP BY rule_id`.
- **Fix:** if the source sent bad rows, wait for the correction and rerun. If a rule is wrong, fix the rule with a test first.
- **Replay:** rerun `ingest-daily`. Ingest overwrites, so reruns never duplicate.

### Stale source (no new rows for more than 2 trading days)

- **Check:** the last date in `silver.qqq_prices` and `silver.vol_indices`, and the source's website. FRED often lags a day.
- **Fix:** nothing if it's a holiday or a FRED lag. Otherwise check the source and the network.
- **Replay:** rerun `ingest-daily` once the source is back. Scoring is skipped while inputs are stale, and the brief and page say the data is delayed.

### Model health (rolling 63-day MAE above 1.5× the backtest MAE)

- **Check:** data first (quarantine, stale sources), then the market regime (is this a crisis like 2008 or 2020?).
- **Fix:** if the data is fine and the regime has shifted for months, rerun the backtest and confirm the champion.
- **Replay:** `databricks bundle run qqq_volatility_forecaster_backtest -t pr`, then commit the new `results/summary.json` through a PR.

## Service level objective

Gold tables refreshed by 01:00 UTC the next day on at least 95% of trading days. Measured from `ops.run_log`.

## First-time setup

1. Create a Databricks Free Edition workspace with a personal account.
2. Create the catalogs with SQL on the warehouse: `CREATE CATALOG qqq_volatility_forecaster_dv` and `CREATE CATALOG qqq_volatility_forecaster_pr`. The CLI can't create catalogs on Free Edition default storage.
3. `databricks bundle deploy -t dv`, then upload `data/bronze/*.csv` to `/Volumes/qqq_volatility_forecaster_dv/bronze/raw/`.
4. Run `qqq_volatility_forecaster_backtest`, then `qqq_volatility_forecaster_daily`.
5. Add GitHub secrets `DATABRICKS_HOST` and `DATABRICKS_TOKEN` (90-day token). `ANTHROPIC_API_KEY` is optional; without it the brief uses the template.
6. Turn on GitHub Pages with "GitHub Actions" as the source.
