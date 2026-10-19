# QQQ Volatility Forecaster

Predicts how much QQQ will swing over the next month, checks if that beats the obvious guess, and measures how often the options market overprices the swing.

## Results

Tested only on years the models never saw (2007–2026, 4,958 days). Error is the average miss in volatility points.

| Model | Avg error | Better than "last month repeats" | Years it won |
|---|---|---|---|
| Last month repeats (baseline) | 6.22 | — | — |
| VXN (options market's guess) | 6.25 | −0.5% | 12 of 20 |
| **Linear regression (best)** | **4.82** | **22.6%** | **18 of 20** |
| Random forest | 5.07 | 18.5% | 17 of 20 |
| XGBoost | 5.25 | 15.6% | 17 of 20 |

- The simple regression won. The tree models didn't add enough to justify the extra complexity.
- The options market priced a bigger swing than actually happened in **80.4%** of months.
- The worst month (Feb 2020) wiped out about **12 months** of gains for sellers.

From commit `837a186`, data fingerprint `130bd9a534cc0d3b`. Full numbers: `results/summary.json`.

This measures forecasts. It is not a trading strategy or financial advice.

## How it works

1. **Download** QQQ daily prices (Yahoo) and VXN/VIX (FRED). Retries on failure.
2. **Check the data.** Bad rows (duplicate dates, impossible prices, VXN out of range) go to a quarantine table with a reason. Big moves are flagged, not dropped. If data stops updating, the forecast is skipped and everything says "data delayed."
3. **Build features** using only what was known that day: recent volatility (1 week, 1 month, 3 months), VXN, VIX, last month's return, distance from the 1-year high.
4. **Test the models** year by year: train on earlier years, test on the next. The 21 days before each test year are dropped from training so no future answers leak in.
5. **Forecast today** with the winning model.
6. **Write a daily summary** with AI. Every number is checked against the data. If a check fails twice, a plain template is used instead.
7. **Publish** a public page with today's numbers, the summary, and a forecast-vs-actual chart.

Volatility = `100 × sqrt(252/21 × sum of the next 21 squared daily log returns)`. VXN is built from Nasdaq-100 options, not QQQ options, but they track closely.

## Run it

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements-dev.txt -e .
qqq-volatility-forecaster ingest
qqq-volatility-forecaster backtest
qqq-volatility-forecaster daily
qqq-volatility-forecaster brief
qqq-volatility-forecaster site
pytest
```

Each backtest saves the commit, a fingerprint of the data, and a copy of that data, so any number can be reproduced exactly.

## Where things are

| Folder | What's in it |
|---|---|
| `src/qqq_volatility_forecaster/` | All the logic |
| `notebooks/` | Thin Databricks wrappers |
| `resources/`, `databricks.yml` | Databricks job definitions |
| `.github/workflows/` | Daily jobs, tests, security scans |
| `tests/` | 85 tests |
| `docs/` | Model card, data sources, runbook, AI review, decision records |

## Limits

- Daily closing prices are a rough measure of volatility.
- 2008 and 2020 cause most of the error.

## Credits

Data: Yahoo Finance (personal use), Cboe via FRED. Libraries: pandas, NumPy, scikit-learn, Jinja2 (BSD-3); XGBoost, yfinance, requests, tenacity (Apache-2.0); LangGraph, anthropic (MIT).
