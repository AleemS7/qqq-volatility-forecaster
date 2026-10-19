import re

DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
NUMBER = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?")
ADVICE = re.compile(r"\b(buy|sell|guarantee[sd]?|recommend\w*)\b", re.I)
ALLOWED_CONSTANTS = (21.0, 30.0, 100.0, 500.0)
REQUIRED = ("forecast", "vxn")


def allowed_values(metrics: dict) -> list[float]:
    values = [
        float(v)
        for k, v in metrics.items()
        if isinstance(v, int | float) and not isinstance(v, bool) and k != "run_id"
    ]
    values += [abs(v) for v in values]
    if "share_overpriced" in metrics:
        values.append(100 * float(metrics["share_overpriced"]))
    return values + list(ALLOWED_CONSTANTS)


def _decimals(text: str) -> int:
    return len(text.split(".")[1]) if "." in text else 0


def matches(text: str, value: float) -> bool:
    return abs(float(text) - value) <= 0.5 * 10 ** -_decimals(text) + 1e-9


def verify(draft: str, metrics: dict) -> list[str]:
    errors = []
    if metrics["date"] not in DATE.findall(draft):
        errors.append(f"missing date {metrics['date']}")
    numbers = NUMBER.findall(DATE.sub(" ", draft))
    values = allowed_values(metrics)
    errors += [f"unverified number {n}" for n in numbers if not any(matches(n, v) for v in values)]
    for key in REQUIRED:
        if not any(matches(n, float(metrics[key])) and _decimals(n) >= 1 for n in numbers):
            errors.append(f"missing {key} {metrics[key]}")
    errors += [f"advice word '{word}'" for word in ADVICE.findall(draft)]
    return errors
