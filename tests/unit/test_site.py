import re

import pandas as pd
import pytest

from qqq_volatility_forecaster.site.render import build_chart, chart_series, render_page

METRICS = {
    "status": "ok",
    "date": "2026-10-15",
    "forecast": 18.57,
    "vxn": 22.89,
    "premium": 4.32,
    "champion": "M2",
}
BRIEF = {
    "text": "On 2026-10-15 the forecast was 18.57.",
    "label": "AI-generated, numbers verified.",
}


@pytest.fixture
def series():
    dates = pd.bdate_range("2025-01-01", periods=60)
    frame = pd.DataFrame(
        {
            "date": list(dates.strftime("%Y-%m-%d")) * 2,
            "model": ["M2"] * 60 + ["M0"] * 60,
            "forecast": 18.0,
            "actual": 20.0,
            "vxn": 22.0,
        }
    )
    return chart_series(frame, "M2")


def test_chart_series_keeps_champion_only(series):
    assert len(series) == 60
    assert list(series.columns) == ["date", "forecast", "actual", "vxn"]


def test_chart_has_three_lines_and_spread_labels(series):
    chart = build_chart(series)
    assert [p["label"] for p in chart.svg_paths] == ["Model forecast", "Realized", "VXN"]
    ends = sorted(p["end_y"] for p in chart.svg_paths)
    assert all(b - a >= 14 for a, b in zip(ends, ends[1:], strict=False))


def test_page_shows_todays_numbers(series):
    html = render_page(METRICS, BRIEF, series, pd.Timestamp("2026-10-16"), "https://example.com")
    assert "18.57" in html and "22.89" in html and "+4.32" in html
    assert "AI-generated, numbers verified." in html
    assert "Data delayed" not in html
    assert "Not financial advice" in html
    assert "FRED" in html


def test_stale_data_shows_banner(series):
    html = render_page(METRICS, None, series, pd.Timestamp("2026-10-22"), "https://example.com")
    assert "Data delayed" in html


def test_brief_text_is_escaped(series):
    brief = {**BRIEF, "text": "<script>alert(1)</script>"}
    html = render_page(METRICS, brief, series, pd.Timestamp("2026-10-16"), "https://example.com")
    assert "<script>alert" not in html


def test_page_has_no_secret_like_strings(series):
    html = render_page(METRICS, BRIEF, series, pd.Timestamp("2026-10-16"), "https://example.com")
    assert not re.search(r"sk-ant-|dapi[0-9a-f]{8}|api[_-]?key|token", html, re.I)
    assert "<input" not in html and "<form" not in html
