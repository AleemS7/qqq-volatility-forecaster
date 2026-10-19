# QQQ Volatility Forecaster

Can I predict how much QQQ will swing over the next month better than the obvious guess, and how often does the options market overprice that swing?

## What it predicts

The annualized realized volatility of QQQ's daily log returns over the next 21 trading days, in vol points:

```
r_t = ln(adj_close_t / adj_close_{t-1})
y_t = 100 × sqrt( (252 / 21) × Σ_{i=1..21} r_{t+i}² )
```

VXN at the close of day t is the options market's estimate of the same quantity. VXN is built from Nasdaq-100 index options, not QQQ options. QQQ tracks the index closely, but they are not identical.

## Data

| Source | Series | Terms |
|---|---|---|
| Yahoo Finance via `yfinance` | QQQ daily OHLC, adjusted close, volume | Unofficial wrapper, personal use only |
| FRED (St. Louis Fed) | `VXNCLS`, `VIXCLS` | CBOE data republished by FRED. Source: Cboe Global Markets via FRED |

Raw data is downloaded locally into `data/` and never committed. Holidays in FRED (`.`) become nulls and are never forward-filled.

## Method

- **Features** (known at the close of day t): `rv_5`, `rv_21`, `rv_63`, `vxn`, `vix`, `vxn_minus_rv21`, `ret_21`, `drawdown_252`.
- **Models:** M0 naive (`rv_21`, "last month repeats"), M1 market (`vxn`), M2 linear regression on log `rv_5`, `rv_21`, `rv_63`, `vxn`, M3 random forest, M4 XGBoost. Fitted models predict `log(y)`. No tuning beyond fixed settings.
- **Testing:** walk-forward, expanding window from 2001, one refit per year, first test year 2007. The last 21 trading days before each test year are dropped from training because their targets overlap the test year.
- **Metric:** mean absolute error (MAE) in vol points, overall and per test year.
- **Champion rule:** lowest overall MAE among models that beat M0 in at least 60% of test years. Ties go to the simpler model.
- **Overpricing:** non-overlapping 21-day windows, `premium = vxn_t − y_t`.

## Results

From commit `b571df7`, data through 2026-10-16, 20 test years (2007–2026), 4,958 out-of-sample days. Full output in `results/summary.json` and `results/model_scores.csv`.

| Model | MAE (vol pts) | vs. M0 | Test years beating M0 |
|---|---|---|---|
| M0 Naive: last month repeats | 6.22 | — | — |
| M1 Market: VXN | 6.25 | −0.5% | 12 / 20 |
| **M2 Linear regression (champion)** | **4.82** | **+22.6%** | **18 / 20** |
| M3 Random forest | 5.07 | +18.5% | 17 / 20 |
| M4 XGBoost | 5.25 | +15.6% | 16 / 20 |

The simple regression beat the naive guess by 22.6% and won in 18 of 20 years it never saw. The tree models also beat the baseline but did not add enough to justify the extra complexity. M2 lost to the baseline in 2009 and 2022.

**Overpricing (306 non-overlapping windows, 2001–2026):** VXN priced in a bigger swing than actually happened in 80.4% of windows, with a median premium of 4.4 vol points. The worst window, starting 2020-02-14, came in 66.5 points under realized, which wiped out about 12 months of typical premium-seller gains.

The scoreboard is a proxy. It ignores transaction costs, contract details, and the exact payoff shape. This project measures forecasts. It is not a trading strategy and not financial advice.

## Reproduce

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements-dev.txt -e .
python -m qqq_volatility_forecaster.ingest
python -m qqq_volatility_forecaster
pytest
```

`python -m qqq_volatility_forecaster` writes `results/summary.json` with the commit hash and whether `src/` had uncommitted changes.

## Limitations

- Daily close-to-close returns are a noisy measure of volatility. Intraday data would be better.
- VXN is an index-option measure applied to an ETF.
- About 5,000 test days across 20 years, with only a handful of crisis periods carrying most of the error.

## Licenses

| Dependency | License |
|---|---|
| pandas, NumPy, scikit-learn | BSD-3-Clause |
| XGBoost, yfinance | Apache-2.0 |
| requests | Apache-2.0 |
