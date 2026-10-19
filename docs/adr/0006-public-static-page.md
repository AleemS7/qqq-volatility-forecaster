# 0006: Public static page on GitHub Pages

- **Status:** Accepted, 2026-10-18
- **Context:** Most BI dashboards need a login to view. Any internet-facing page should carry as little risk as possible.
- **Decision:** Publish a static HTML page rebuilt from gold tables after each brief. No backend, no inputs, no JavaScript framework, derived numbers only. A "data delayed" banner replaces stale numbers.
- **Consequences:** One clickable demo. Nothing generated is committed. Low risk: no secrets or raw data on the page, and a test checks for secret-like strings.
