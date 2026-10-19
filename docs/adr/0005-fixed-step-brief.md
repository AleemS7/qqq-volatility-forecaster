# 0005: Fixed-step LangGraph workflow with a number verifier

- **Status:** Accepted, 2026-10-18
- **Context:** Good practice is to use the least autonomous AI option that works. Language models can state numbers that look right but aren't.
- **Decision:** A fixed graph: load metrics, draft, verify, retry once with the list of wrong numbers, then fall back to a template. The model gets only numeric facts and no tools.
- **Consequences:** A brief is published every day. It never contains an unverified number. Easy to explain and test with a fake client.
