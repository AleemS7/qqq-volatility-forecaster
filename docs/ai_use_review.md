# AI use review: daily brief

| Question | Answer |
|---|---|
| What does the AI do? | Writes a 3–4 sentence plain-English summary of the day's numbers |
| Autonomy level | Fixed-step workflow (LangGraph). No tools, no agent loop, no browsing |
| Model | `claude-opus-5-5` through the Anthropic API, behind the `LlmClient` interface. Server-side refusal fallback enabled. Swappable in `config.BRIEF_MODEL` |
| Prompt | `src/qqq_volatility_forecaster/brief/prompts/brief_v1.md`. The version is stored with every brief |
| Data sent | Only numeric fields and the date from `gold.daily_metrics`. Public market data only. No personal or company data |
| Data classification | Public |
| Never sent | API keys, URLs, run IDs, commit hashes, free text from any source |
| Validation | Every number in the draft must match a provided fact within rounding. The date, forecast, and VXN must appear. Advice words fail the draft |
| Failure handling | One retry with the list of wrong numbers. Then a deterministic template. An outage or missing key also produces the template |
| Labeling | Verified output is labeled "AI-generated, numbers verified." The template is labeled "Template summary." |
| Human oversight | Informational only, never advice. The prompt, verifier, and evaluation results are reviewed through PRs |
| Quality bar | At least 95% of the 20-day evaluation set verified within 2 attempts (`results/brief_eval.json`) |
| Adversarial tests | Altered number caught, missing fact caught, outage produces the template (`tests/unit/test_brief_graph.py`, `test_verifier.py`) |
| Risks | Wrong numbers (blocked by the verifier). Advice-like tone (blocked by word checks and the prompt). Prompt injection (no free-text inputs) |
