import logging
import os

import pandas as pd

from qqq_volatility_forecaster import config
from qqq_volatility_forecaster.io.tables import read_table, table_exists
from qqq_volatility_forecaster.ops import RunLog
from qqq_volatility_forecaster.pipeline.brief import latest_metrics
from qqq_volatility_forecaster.site.render import chart_series, render_page, write_site

log = logging.getLogger(__name__)

SITE_DIR = config.ROOT / "site"


def _repo_url() -> str:
    repository = os.environ.get("GITHUB_REPOSITORY")
    return f"https://github.com/{repository}#readme" if repository else "../README.md"


def _brief_for(date: str) -> dict | None:
    if not table_exists("gold", "daily_brief"):
        return None
    briefs = read_table("gold", "daily_brief", dated=False)
    match = briefs[briefs["date"].astype(str) == date]
    return match.iloc[-1].to_dict() if not match.empty else None


def run_site(run_log: RunLog) -> None:
    with run_log.step("site:render") as record:
        metrics = latest_metrics()
        predictions = read_table("gold", "backtest_predictions", dated=False)
        series = chart_series(predictions, metrics["champion"])
        html = render_page(
            metrics,
            _brief_for(str(metrics["date"])),
            series,
            pd.Timestamp.today().normalize(),
            _repo_url(),
        )
        path = write_site(html, SITE_DIR)
        record["rows_out"] = len(series)
    log.info("Wrote %s", path)
