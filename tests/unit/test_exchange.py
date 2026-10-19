import pandas as pd

from qqq_volatility_forecaster import config
from qqq_volatility_forecaster.io.tables import read_table, table_name, write_table
from qqq_volatility_forecaster.ops import RunLog
from qqq_volatility_forecaster.pipeline.exchange import export_tables, import_brief, load_raw_files


def test_table_name(monkeypatch):
    monkeypatch.delenv("QQQ_VOL_CATALOG", raising=False)
    assert table_name("gold", "forecasts") == f"{config.CATALOG}.gold.forecasts"
    assert table_name("snapshots/abc", "qqq_prices") == f"{config.CATALOG}.snapshots.abc_qqq_prices"


def test_dated_reads_come_back_sorted(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    shuffled = pd.DataFrame({"date": ["2024-01-03", "2024-01-01", "2024-01-02"], "x": [3, 1, 2]})
    write_table(shuffled, "silver", "t", index=False)
    assert read_table("silver", "t")["x"].tolist() == [1, 2, 3]


def test_round_trip_through_volume(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path / "data")
    volume = tmp_path / "volume"
    volume.mkdir()
    dates = pd.bdate_range("2024-01-01", periods=2, name="date")
    pd.DataFrame({"adj_close": [1.0, 2.0]}, index=dates).to_csv(volume / "qqq_prices.csv")
    pd.DataFrame({"VXNCLS": [20.0, 21.0]}, index=dates).to_csv(volume / "vol_indices.csv")

    load_raw_files(volume, RunLog())
    assert read_table("bronze", "qqq_prices")["adj_close"].tolist() == [1.0, 2.0]

    write_table(
        pd.DataFrame([{"date": "2024-01-02", "forecast": 18.0}]),
        "gold",
        "daily_metrics",
        index=False,
    )
    exports = tmp_path / "exports"
    assert [p.name for p in export_tables(exports)] == ["daily_metrics.csv"]

    pd.DataFrame([{"date": "2024-01-02", "text": "hi", "status": "fallback"}]).to_csv(
        exports / "daily_brief.csv", index=False
    )
    assert import_brief(exports) == 1
    assert import_brief(tmp_path / "missing") == 0
