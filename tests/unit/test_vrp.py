import numpy as np
import pandas as pd
import pytest

from qvol.features.build import build_features
from qvol.vrp.analysis import vrp_stats, vrp_windows


def test_windows_do_not_overlap(market):
    frame = build_features(*market)
    windows = vrp_windows(frame, horizon=21)
    positions = frame.index.get_indexer(windows.index)
    assert (np.diff(positions) >= 21).all()


def test_stats():
    dates = pd.bdate_range("2020-01-01", periods=5)
    frame = pd.DataFrame(
        {"vxn": [20.0, 20.0, 20.0, 20.0, 20.0], "y": [18.0, 17.0, 16.0, 40.0, 18.0]},
        index=dates,
    )
    stats = vrp_stats(vrp_windows(frame, horizon=1))
    assert stats["share_overpriced"] == pytest.approx(0.8)
    assert stats["typical_gain"] == pytest.approx(2.5)
    assert stats["worst_premium"] == pytest.approx(-20.0)
    assert stats["worst_window_months_erased"] == pytest.approx(8.0)
    assert stats["max_scoreboard_drawdown"] == pytest.approx(20.0)
