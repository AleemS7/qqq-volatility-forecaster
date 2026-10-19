import pandas as pd
import pytest

from qvol.models.evaluate import model_scores, pick_champion, summarize


def _scores(yearly: dict[str, list[float]]) -> pd.DataFrame:
    rows = [
        {"model": model, "year": 2007 + i, "mae": mae, "rows": 1}
        for model, maes in yearly.items()
        for i, mae in enumerate(maes)
    ]
    rows += [
        {"model": model, "year": "overall", "mae": sum(maes) / len(maes), "rows": len(maes)}
        for model, maes in yearly.items()
    ]
    return pd.DataFrame(rows)


def test_model_scores_mae():
    predictions = pd.DataFrame(
        {
            "model": ["M0", "M0", "M0"],
            "year": [2007, 2007, 2008],
            "forecast": [10.0, 20.0, 30.0],
            "actual": [12.0, 16.0, 30.0],
        }
    )
    scores = model_scores(predictions).set_index(["model", "year"])["mae"]
    assert scores[("M0", 2007)] == pytest.approx(3.0)
    assert scores[("M0", 2008)] == pytest.approx(0.0)
    assert scores[("M0", "overall")] == pytest.approx(2.0)


def test_summary_counts_years_beaten():
    summary = summarize(_scores({"M0": [5, 5, 5, 5, 5], "M2": [4, 4, 4, 6, 6]}))
    assert summary.loc["M2", "years_beat_baseline"] == 3
    assert summary.loc["M2", "beat_share"] == pytest.approx(0.6)
    assert summary.loc["M2", "improvement_pct"] == pytest.approx(4.0)


def test_champion_needs_lowest_mae_and_enough_years():
    summary = summarize(
        _scores(
            {
                "M0": [5, 5, 5, 5, 5],
                "M2": [4.5, 4.5, 4.5, 4.5, 4.5],
                "M4": [1, 1, 6, 6, 6],
            }
        )
    )
    assert pick_champion(summary) == "M2"


def test_champion_tie_goes_to_simpler_model():
    summary = summarize(_scores({"M0": [5, 5], "M2": [4, 4], "M3": [4, 4], "M4": [4.001, 4.001]}))
    assert pick_champion(summary) == "M2"


def test_baseline_is_champion_when_nothing_beats_it():
    summary = summarize(_scores({"M0": [4, 4], "M2": [5, 5]}))
    assert pick_champion(summary) == "M0"
