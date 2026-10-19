import pandas as pd

from qvol.config import CHAMPION_MIN_BEAT_SHARE

BASELINE = "M0"


def model_scores(predictions: pd.DataFrame) -> pd.DataFrame:
    errors = predictions.assign(abs_error=(predictions["forecast"] - predictions["actual"]).abs())
    by_year = (
        errors.groupby(["model", "year"])
        .agg(mae=("abs_error", "mean"), rows=("abs_error", "size"))
        .reset_index()
    )
    overall = (
        errors.groupby("model")
        .agg(mae=("abs_error", "mean"), rows=("abs_error", "size"))
        .reset_index()
        .assign(year="overall")
    )
    return pd.concat([by_year, overall], ignore_index=True)


def summarize(scores: pd.DataFrame, baseline: str = BASELINE) -> pd.DataFrame:
    yearly = scores[scores["year"] != "overall"].pivot(index="year", columns="model", values="mae")
    overall = scores[scores["year"] == "overall"].set_index("model")["mae"]
    beats = yearly.lt(yearly[baseline], axis=0)
    summary = pd.DataFrame(
        {
            "mae": overall,
            "years_beat_baseline": beats.sum(),
            "test_years": len(yearly),
            "improvement_pct": 100 * (overall[baseline] - overall) / overall[baseline],
        }
    )
    summary["beat_share"] = summary["years_beat_baseline"] / summary["test_years"]
    return summary.loc[sorted(summary.index)]


def pick_champion(
    summary: pd.DataFrame,
    baseline: str = BASELINE,
    min_share: float = CHAMPION_MIN_BEAT_SHARE,
    decimals: int = 2,
) -> str:
    eligible = summary[(summary.index != baseline) & (summary["beat_share"] >= min_share)]
    eligible = eligible[eligible["mae"] < summary.loc[baseline, "mae"]]
    if eligible.empty:
        return baseline
    ranked = eligible.assign(rounded=eligible["mae"].round(decimals), order=eligible.index)
    return ranked.sort_values(["rounded", "order"]).index[0]
