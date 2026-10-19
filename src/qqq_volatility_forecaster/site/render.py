import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from jinja2 import Environment, PackageLoader, select_autoescape

from qqq_volatility_forecaster.quality.rules import is_stale

SERIES = (("forecast", "Model forecast"), ("actual", "Realized"), ("vxn", "VXN"))
WIDTH, HEIGHT = 720, 300
MARGIN = {"left": 40, "right": 96, "top": 16, "bottom": 28}
HIT_STEP = 5


@dataclass
class Chart:
    svg_paths: list[dict]
    gridlines: list[dict]
    ticks: list[dict]
    hits: list[dict]
    width: int = WIDTH
    height: int = HEIGHT
    plot_left: int = MARGIN["left"]
    plot_right: int = WIDTH - MARGIN["right"]


def chart_series(predictions: pd.DataFrame, champion: str, days: int = 504) -> pd.DataFrame:
    rows = predictions[predictions["model"] == champion].sort_values("date").tail(days)
    return rows[["date", "forecast", "actual", "vxn"]].reset_index(drop=True)


def build_chart(series: pd.DataFrame) -> Chart:
    plot_w = WIDTH - MARGIN["left"] - MARGIN["right"]
    plot_h = HEIGHT - MARGIN["top"] - MARGIN["bottom"]
    top = max(10, math.ceil(series[["forecast", "actual", "vxn"]].max().max() / 10) * 10)
    xs = MARGIN["left"] + np.linspace(0, plot_w, len(series))

    def y(value: float) -> float:
        return MARGIN["top"] + plot_h * (1 - value / top)

    paths = []
    for index, (column, label) in enumerate(SERIES, start=1):
        values = series[column].to_numpy(dtype=float)
        points = " ".join(f"{x:.1f},{y(v):.1f}" for x, v in zip(xs, values, strict=True))
        paths.append(
            {"slot": index, "label": label, "points": points, "end_y": round(y(values[-1]), 1)}
        )
    spread_labels(paths)

    gridlines = [{"y": round(y(v), 1), "label": v} for v in range(0, top + 1, 10)]
    dates = pd.to_datetime(series["date"])
    ticks = [
        {"x": round(xs[i], 1), "label": dates[i].strftime("%b %Y")}
        for i in range(1, len(dates))
        if dates[i].month in (1, 7) and dates[i - 1].month != dates[i].month
    ]
    hits = []
    for start in range(0, len(series), HIT_STEP):
        row = series.iloc[start]
        hits.append(
            {
                "x": round(xs[start], 1),
                "width": round(plot_w / len(series) * HIT_STEP, 1),
                "title": (
                    f"{pd.Timestamp(row['date']).date()}: forecast {row['forecast']:.1f}, "
                    f"realized {row['actual']:.1f}, VXN {row['vxn']:.1f}"
                ),
            }
        )
    return Chart(paths, gridlines, ticks, hits)


def spread_labels(paths: list[dict], gap: float = 14.0) -> None:
    ordered = sorted(paths, key=lambda p: p["end_y"])
    for above, below in zip(ordered, ordered[1:], strict=False):
        below["end_y"] = max(below["end_y"], above["end_y"] + gap)


def render_page(
    metrics: dict,
    brief: dict | None,
    series: pd.DataFrame,
    as_of: pd.Timestamp,
    repo_url: str,
) -> str:
    env = Environment(
        loader=PackageLoader("qqq_volatility_forecaster.site"),
        autoescape=select_autoescape(["html", "j2"]),
    )
    stale = metrics.get("status") != "ok" or is_stale(pd.Timestamp(metrics["date"]), as_of)
    table = series.tail(10).iloc[::-1].round(2).to_dict(orient="records")
    return env.get_template("index.html.j2").render(
        metrics=metrics,
        brief=brief,
        chart=build_chart(series),
        table=table,
        stale=stale,
        repo_url=repo_url,
        updated=as_of.date(),
    )


def write_site(html: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "index.html"
    path.write_text(html, encoding="utf-8")
    return path
