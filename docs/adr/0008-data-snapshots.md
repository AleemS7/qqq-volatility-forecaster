# 0008: Snapshot backtest inputs by fingerprint

- **Status:** Accepted, 2026-10-18
- **Context:** Yahoo's adjusted closes change in the 4th decimal between downloads. That moves tree-model scores by about 0.01 vol points, so a fresh download can't reproduce a number exactly.
- **Decision:** Round prices to 4 decimals at ingest. Hash the backtest's inputs, save them under `data/snapshots/<fingerprint>/`, and record the fingerprint and commit in `results/summary.json`.
- **Consequences:** Any reported number reproduces exactly from its commit and snapshot. Headline results are stable across downloads.
