# Data sources

| Source | Series | Access | Frequency | Terms |
|---|---|---|---|---|
| Yahoo Finance via `yfinance` | QQQ open, high, low, close, adjusted close, volume | `yf.download("QQQ", auto_adjust=False)` | Daily since 1999-03-10 | Unofficial wrapper around Yahoo's public endpoints. Personal, non-commercial use only. Not redistributed |
| FRED, Federal Reserve Bank of St. Louis | `VXNCLS` (Cboe Nasdaq-100 Volatility Index) | `https://fred.stlouisfed.org/graph/fredgraph.csv?id=VXNCLS` | Daily close since 2001-02-02 | Source: Cboe Global Markets via FRED. Cite both |
| FRED | `VIXCLS` (Cboe Volatility Index) | `https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS` | Daily close since 1990 | Same as above |

## Handling rules

- Raw data is never committed to Git. Local copies live in `data/`, which is ignored.
- Every bronze row carries `_source`, `_ingested_at`, and `_run_id`.
- FRED holidays (`.`) become nulls and are never forward-filled.
- Prices are rounded to 4 decimals at ingest. Yahoo's adjusted closes shift slightly between downloads, so each backtest also saves its exact input under `data/snapshots/<fingerprint>/` and records the fingerprint in `results/summary.json`.
- The trading calendar is the set of dates in the QQQ price data.

## Lineage

```
yahoo / fred → bronze.qqq_prices, bronze.vol_indices
            → silver (rule-checked) + ops.quarantine
            → gold.features_daily → gold.forecasts, gold.daily_metrics
            → gold.backtest_predictions, gold.model_scores, gold.vrp_windows
            → gold.daily_brief → GitHub Pages
```
