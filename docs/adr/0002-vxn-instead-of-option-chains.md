# 0002: Use VXN as the options-market signal

- **Status:** Accepted, 2026-10-18
- **Context:** Historical QQQ option chains are not available for free. Collecting them live adds a second scheduled job and six quality rules.
- **Decision:** Use VXN, the options market's own 30-day volatility estimate for the Nasdaq-100, as the implied-volatility benchmark.
- **Consequences:** The project stays about options without chain data. VXN is built from index options, not QQQ options, which the README states.
