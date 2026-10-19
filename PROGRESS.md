# Progress

## 2026-10-18

Core tier done on `feature/1-core-backtest`: ingest, target, features, walk-forward M0–M4, champion rule, overpricing analysis. 16 unit tests pass. Results reproduce byte-for-byte from commit `b571df7`.

Next:

- Rewrite by hand: `realized_vol`, `forward_realized_vol`, `walk_forward_splits`.
- LEARNING.md entry for Phase 1.
- Data quality rules (section 7) before Phase 2.
- Merge to `develop`, tag `v0.1.0`.
