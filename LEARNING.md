# Learning notes

Read these until you can say each one without looking.

## Phase 1: Core

**Realized volatility.** Take each day's log return, square it, add up 21 of them, scale by 252/21 to make it a yearly number, take the square root, and multiply by 100. That's `realized_vol` in `features/volatility.py`. The target `y` is the same calculation on the *next* 21 days, which is why `forward_realized_vol` shifts the result back by 21 rows.

**Why the gap.** The target for a day in mid-December covers returns in January. If that row trains a model tested on January, the model has seen January's answer. Dropping the last 21 training rows before each test year removes that overlap. `walk_forward_splits` does this, and `test_no_training_target_window_reaches_the_test_year` proves it.

**Leakage test.** Scramble every price and index value after some day and rebuild the features. If any feature on or before that day changes, a feature is peeking at the future. `test_changing_the_future_does_not_change_todays_features` does this.

**Baseline first.** "Last month repeats" (M0) is hard to beat because volatility is sticky. A model only counts if it beats M0 on years it never saw. The linear regression did, by 22.6%, in 18 of 20 years.

**Bagging vs. boosting.** A random forest averages many independent trees (bagging). XGBoost builds trees one after another, each fixing the last one's mistakes (boosting). Neither beat the regression here, because most of the signal is recent volatility, which a straight line already captures.

**Overpricing.** Compare VXN on a day with what actually happened over the next 21 days. Use windows that don't overlap so the same month isn't counted 21 times. VXN was higher 80% of the time. The worst miss (February 2020) wiped out about a year of typical gains.

## Phase 2: Pipeline

**Bronze, silver, gold.** Bronze is what came in, plus where and when. Silver is checked and cleaned. Gold is what people use: features, forecasts, scores, the brief.

**Quarantine instead of delete.** A bad row (a low above the high, a zero price, a duplicate date) goes to `ops.quarantine` with the rule that caught it. A big move is only flagged, because real crashes happen.

**Stale data.** If a source hasn't updated in more than 2 trading days, scoring is skipped and the brief and page say the data is delayed instead of showing old numbers as current.

**Retries.** Each download tries up to 4 times, waiting 2, 4, then 8 seconds. After that the source is marked stale and the other source still runs.

**Why ingest runs in GitHub Actions.** Databricks Free Edition blocks most outbound internet, so GitHub downloads the files and drops them in a volume for Databricks to pick up.

## Phase 4: Brief

**Fixed steps, not an agent.** Load the numbers, draft, check every number, retry once with the list of mistakes, otherwise use a template. The model gets numbers only, no tools, no keys.

**The checker.** Pull every number out of the draft. Each one must match a fact within rounding (18.6 is fine for 18.57, 18.5 is not). The date, forecast, and VXN must appear. Words like "buy" or "sell" fail it.

## Phase 5: Page

**Static on purpose.** One HTML file rebuilt after each brief. No backend, no inputs, nothing to log into. If the data is old, a banner says so.
