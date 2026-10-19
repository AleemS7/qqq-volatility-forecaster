from collections.abc import Callable
from importlib.resources import files
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from qqq_volatility_forecaster import config
from qqq_volatility_forecaster.brief.llm_client import LlmClient, LlmError
from qqq_volatility_forecaster.brief.verifier import verify

LABEL = "AI-generated, numbers verified."
FACT_LABELS = {
    "date": "Date",
    "forecast": "Model forecast of realized volatility, next 21 trading days (vol points)",
    "vxn": "VXN, options-implied volatility for the Nasdaq-100 (vol points)",
    "vix": "VIX, options-implied volatility for the S&P 500 (vol points)",
    "rv_21": "QQQ realized volatility over the past 21 trading days (vol points)",
    "premium": "VXN minus the model forecast (vol points)",
    "backtest_mae": "Model average error in backtesting (vol points)",
    "share_overpriced_pct": "Share of past months where VXN exceeded realized volatility (%)",
}


class BriefState(TypedDict, total=False):
    metrics: dict
    facts: dict
    draft: str
    errors: list[str]
    attempts: int
    status: str
    model_id: str
    prompt_version: str


def load_prompt(version: str = config.BRIEF_PROMPT_VERSION) -> tuple[str, str]:
    text = (files("qqq_volatility_forecaster.brief") / "prompts" / f"{version}.md").read_text()
    system, user = text.split("# user", 1)
    return system.replace("# system", "").strip(), user.strip()


def to_facts(metrics: dict) -> dict:
    facts = {key: metrics[key] for key in FACT_LABELS if key in metrics}
    if "share_overpriced" in metrics:
        facts["share_overpriced_pct"] = round(100 * float(metrics["share_overpriced"]), 1)
    return facts


def fallback_text(state: BriefState) -> str:
    metrics = state["metrics"]
    if metrics.get("status") != "ok":
        return f"Data delayed. The latest available market data is from {metrics['date']}."
    return (
        f"On {metrics['date']}, the model forecast QQQ volatility over the next 21 trading days "
        f"at {metrics['forecast']:.2f} vol points. VXN, the options market's estimate for the "
        f"same period, closed at {metrics['vxn']:.2f}, a gap of {metrics['premium']:.2f} points."
    )


def build_graph(llm: LlmClient, load_metrics: Callable[[], dict]):
    system, template = load_prompt()

    def load(state: BriefState) -> BriefState:
        metrics = load_metrics()
        return {
            "metrics": metrics,
            "facts": to_facts(metrics),
            "attempts": 0,
            "errors": [],
            "model_id": llm.model_id,
            "prompt_version": config.BRIEF_PROMPT_VERSION,
        }

    def draft(state: BriefState) -> BriefState:
        facts = "\n".join(f"- {FACT_LABELS[k]}: {v}" for k, v in state["facts"].items())
        corrections = ""
        if state["errors"]:
            corrections = "\nYour previous draft failed these checks. Fix them:\n" + "\n".join(
                f"- {e}" for e in state["errors"]
            )
        prompt = template.format(facts=facts, corrections=corrections)
        try:
            text = llm.complete(system, prompt)
        except LlmError as error:
            return {
                "draft": "",
                "errors": [f"llm error: {error}"],
                "attempts": state["attempts"] + 1,
            }
        return {"draft": text, "errors": [], "attempts": state["attempts"] + 1}

    def check(state: BriefState) -> BriefState:
        if state["errors"] and state["errors"][0].startswith("llm error"):
            return {}
        return {"errors": verify(state["draft"], state["facts"])}

    def fallback(state: BriefState) -> BriefState:
        return {"draft": fallback_text(state), "status": "fallback"}

    def publish(state: BriefState) -> BriefState:
        return {"status": state.get("status") or "llm_verified"}

    def after_load(state: BriefState) -> str:
        return "draft" if state["metrics"].get("status") == "ok" else "fallback_template"

    def after_verify(state: BriefState) -> str:
        if not state["errors"]:
            return "publish"
        return "draft" if state["attempts"] < config.BRIEF_MAX_ATTEMPTS else "fallback_template"

    graph = StateGraph(BriefState)
    graph.add_node("load_metrics", load)
    graph.add_node("draft", draft)
    graph.add_node("verify", check)
    graph.add_node("fallback_template", fallback)
    graph.add_node("publish", publish)
    graph.add_edge(START, "load_metrics")
    graph.add_conditional_edges("load_metrics", after_load, ["draft", "fallback_template"])
    graph.add_edge("draft", "verify")
    graph.add_conditional_edges("verify", after_verify, ["publish", "draft", "fallback_template"])
    graph.add_edge("fallback_template", "publish")
    graph.add_edge("publish", END)
    return graph.compile()
