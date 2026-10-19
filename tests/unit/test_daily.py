import numpy as np
import pandas as pd
import pytest

from qqq_volatility_forecaster.features.build import build_features
from qqq_volatility_forecaster.pipeline.daily import forecast_latest, mature_forecasts, model_health


def test_forecast_latest_scores_the_last_complete_day(market):
    prices, indices = market
    indices = indices.copy()
    indices.iloc[-1, 0] = np.nan
    frame = build_features(prices, indices)
    today, _ = forecast_latest(frame, "M2")
    assert today == prices.index[-2]


def test_naive_forecast_is_rv21(market):
    frame = build_features(*market)
    today, forecast = forecast_latest(frame, "M0")
    assert forecast == pytest.approx(frame.loc[today, "rv_21"])


def test_mature_forecasts_fills_realized_when_known():
    frame = pd.DataFrame(
        {"y": [20.0, np.nan]}, index=pd.DatetimeIndex(["2024-01-02", "2024-01-03"])
    )
    forecasts = pd.DataFrame({"date": ["2024-01-02", "2024-01-03"], "forecast": [18.0, 19.0]})
    matured = mature_forecasts(forecasts, frame)
    assert matured["realized"].iloc[0] == 20.0
    assert np.isnan(matured["realized"].iloc[1])


@pytest.mark.parametrize(("error", "status"), [(3.0, "ok"), (7.6, "alert")])
def test_model_health(error, status):
    forecasts = pd.DataFrame({"forecast": [20.0] * 30, "realized": [20.0 + error] * 30})
    assert model_health(forecasts, backtest_mae=5.0)["status"] == status


def test_model_health_needs_enough_matured_rows():
    forecasts = pd.DataFrame({"forecast": [20.0] * 10, "realized": [30.0] * 10})
    assert model_health(forecasts, backtest_mae=5.0)["status"] == "insufficient"
