import pandas as pd
import pytest

from qqq_volatility_forecaster import config
from qqq_volatility_forecaster.ingest import run as ingest_run
from qqq_volatility_forecaster.io.tables import read_table
from qqq_volatility_forecaster.ops import RunLog
from qqq_volatility_forecaster.pipeline import backtest as backtest_module
from qqq_volatility_forecaster.pipeline.daily import run_daily
from qqq_volatility_forecaster.pipeline.silver import build_silver
from tests.conftest import synthetic_market


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    prices, indices = synthetic_market(2600)
    prices.iloc[100, prices.columns.get_loc("low")] = prices.iloc[100]["high"] + 1
    monkeypatch.setattr(config, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(config, "RESULTS_DIR", tmp_path / "results")
    monkeypatch.setattr(backtest_module, "SUMMARY_PATH", tmp_path / "results" / "summary.json")
    monkeypatch.setattr(
        ingest_run, "SOURCES", {"qqq_prices": lambda: prices, "vol_indices": lambda: indices}
    )
    return prices


def test_ingest_to_daily_forecast(workspace):
    run_log = RunLog()
    ingest_run.ingest(run_log)
    as_of = workspace.index.max()
    silver = build_silver(run_log, as_of=as_of)
    assert len(silver.prices) == len(workspace) - 1

    report = backtest_module.run_backtest(silver.prices, silver.indices, run_log)
    assert report["data"]["test_years"] == [2007, 2008, 2009]
    assert set(report["models"]) == {"M0", "M1", "M2", "M3", "M4"}

    metrics = run_daily(silver, backtest_module.load_summary(), run_log)
    assert metrics["status"] == "ok"
    assert metrics["forecast"] > 0

    quarantine = read_table("ops", "quarantine", dated=False)
    assert "DQ-P02" in set(quarantine["rule_id"])
    assert set(run_log.frame()["status"]) == {"success"}
    assert len(read_table("gold", "forecasts", dated=False)) == 1
    assert (
        read_table("gold", "backtest_runs", dated=False)["champion"].iloc[-1] == report["champion"]
    )


def test_stale_inputs_skip_scoring(workspace):
    run_log = RunLog()
    ingest_run.ingest(run_log)
    silver = build_silver(run_log, as_of=workspace.index.max() + pd.offsets.BDay(5))
    backtest_module.run_backtest(silver.prices, silver.indices, run_log)
    metrics = run_daily(silver, backtest_module.load_summary(), run_log)
    assert metrics["status"] == "delayed"
    assert "qqq_prices" in silver.stale


def test_failed_source_is_marked_stale(workspace, monkeypatch):
    def broken():
        raise ConnectionError("down")

    monkeypatch.setattr(ingest_run, "SOURCES", {"qqq_prices": broken})
    run_log = ingest_run.ingest(RunLog())
    assert run_log.frame()["status"].tolist() == ["stale"]
