# 0003: Walk-forward testing with a 21-day gap, scored by MAE

- **Status:** Accepted, 2026-10-18
- **Context:** Random splits leak future information in time series. Each target covers the next 21 trading days, so rows right before a test year overlap it.
- **Decision:** Expanding window from 2001, one refit per year, first test year 2007. Drop the last 21 trading days before each test year from training. One metric: MAE in vol points, overall and per year.
- **Consequences:** Every reported number comes from years the model never saw. MAE is easy to explain. Per-year counts show whether a win is consistent or driven by one crisis.
