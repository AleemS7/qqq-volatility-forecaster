import pytest

from qqq_volatility_forecaster.brief.verifier import matches, verify

FACTS = {
    "date": "2026-10-15",
    "forecast": 18.57,
    "vxn": 22.89,
    "vix": 16.46,
    "rv_21": 16.62,
    "premium": 4.32,
    "share_overpriced_pct": 80.4,
}

GOOD = (
    "On 2026-10-15 the model expects QQQ to swing at 18.57 vol points over the next 21 trading "
    "days. VXN, the options market's estimate, closed at 22.89, about 4.3 points higher. "
    "VXN has run above realized volatility in 80.4% of past months."
)


def test_exact_numbers_pass():
    assert verify(GOOD, FACTS) == []


@pytest.mark.parametrize(
    ("text", "value", "ok"),
    [("18.6", 18.57, True), ("19", 18.57, True), ("18.5", 18.57, False), ("80", 80.4, True)],
)
def test_rounding_tolerance(text, value, ok):
    assert matches(text, value) == ok


def test_altered_number_is_caught():
    errors = verify(GOOD.replace("22.89", "23.89"), FACTS)
    assert "unverified number 23.89" in errors
    assert "missing vxn 22.89" in errors


def test_invented_number_is_caught():
    assert verify(GOOD + " Volatility rose 12.5% this week.", FACTS) == ["unverified number 12.5"]


def test_missing_date_fails():
    assert verify(GOOD.replace("On 2026-10-15 the", "The"), FACTS) == ["missing date 2026-10-15"]


def test_missing_forecast_fails():
    text = "On 2026-10-15 VXN closed at 22.89."
    assert verify(text, FACTS) == ["missing forecast 18.57"]


@pytest.mark.parametrize("word", ["buy", "Sell", "guaranteed", "recommend"])
def test_advice_words_rejected(word):
    assert f"advice word '{word}'" in verify(f"{GOOD} You should {word} now.", FACTS)


def test_sellers_is_not_advice():
    assert verify(GOOD + " Option sellers collect that gap.", FACTS) == []


def test_index_names_are_allowed():
    assert verify(GOOD + " VXN tracks the Nasdaq-100 and VIX the S&P 500.", FACTS) == []
