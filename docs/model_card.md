# Model card: QQQ Volatility Forecaster

## Purpose

Forecast QQQ's annualized realized volatility over the next 21 trading days and compare it with VXN, the options market's estimate for the same period. Informational only. Not a trading signal.

## Target

`y_t = 100 × sqrt((252 / 21) × Σ_{i=1..21} r_{t+i}²)`, where `r` is the daily log return of QQQ's adjusted close. Units are vol points.

## Inputs

All known at the close of day t: `rv_5`, `rv_21`, `rv_63`, `vxn`, `vix`, `vxn_minus_rv21`, `ret_21`, `drawdown_252`. Sources and terms are in `data_sources.md`.

## Models

| ID | Model | Inputs | Settings |
|---|---|---|---|
| M0 | Naive: last month repeats | `rv_21` | none |
| M1 | Market: VXN | `vxn` | none |
| M2 | Linear regression (HAR) | log of `rv_5`, `rv_21`, `rv_63`, `vxn` | ordinary least squares |
| M3 | Random forest | all 8 features | 300 trees, depth 6, 20 samples per leaf |
| M4 | XGBoost | all 8 features | 300 trees, depth 3, learning rate 0.05, subsample 0.8 |

Fitted models predict `log(y)` and are converted back with `exp`. No tuning beyond these fixed settings.

## Evaluation

- Walk-forward with an expanding window from 2001, refit once a year, test years 2007 onward.
- The last 21 trading days before each test year are dropped from training because their targets overlap the test year.
- Metric: mean absolute error in vol points, overall and per test year.
- Champion rule: lowest overall MAE among models that beat M0 in at least 60% of test years, ties to the simpler model.
- Current results and the commit and data fingerprint that produced them: `results/summary.json`.

## Champion

M2, the linear regression. It beat the naive guess in 18 of 20 test years. The tree models also beat the baseline but did not beat M2.

## Known limitations

- Close-to-close returns are a noisy volatility measure.
- VXN is built from Nasdaq-100 index options, not QQQ options.
- A handful of crisis windows (2008, 2020) carry much of the error. M2 lost to the baseline in 2009 and 2022.
- About 5,000 test days. Small differences between models (under about 0.1 vol points) are not meaningful.

## Monitoring

Rolling 63-day MAE of matured live forecasts. Alert when it exceeds 1.5× the backtest MAE. See `runbook.md`.
