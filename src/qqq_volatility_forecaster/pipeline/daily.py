import logging

import numpy as np
import pandas as pd

from qqq_volatility_forecaster.features.build import FEATURES, TARGET, build_features
from qqq_volatility_forecaster.io.tables import upsert_table, write_table
from qqq_volatility_forecaster.models.train import MODELS
from qqq_volatility_forecaster.ops import RunLog
from qqq_volatility_forecaster.pipeline.silver import Silver

log = logging.getLogger(__name__)

HEALTH_WINDOW = 63
HEALTH_MIN_ROWS = 21
HEALTH_RATIO = 1.5


def forecast_latest(frame: pd.DataFrame, model_id: str) -> tuple[pd.Timestamp, float]:
    spec = MODELS[model_id]
    train = frame.dropna(subset=FEATURES + [TARGET])
    ready = frame.dropna(subset=FEATURES)
    today = ready.index.max()
    model = spec.make().fit(train[spec.columns], np.log(train[TARGET]))
    return today, float(np.exp(model.predict(ready.loc[[today], spec.columns]))[0])


def mature_forecasts(forecasts: pd.DataFrame, frame: pd.DataFrame) -> pd.DataFrame:
    dates = pd.to_datetime(forecasts["date"])
    return forecasts.assign(realized=frame[TARGET].reindex(dates).to_numpy())


def model_health(forecasts: pd.DataFrame, backtest_mae: float) -> dict:
    matured = forecasts.dropna(subset=["realized"]).tail(HEALTH_WINDOW)
    if len(matured) < HEALTH_MIN_ROWS:
        return {"status": "insufficient", "matured_rows": len(matured), "rolling_mae": None}
    mae = float((matured["forecast"] - matured["realized"]).abs().mean())
    status = "alert" if mae > HEALTH_RATIO * backtest_mae else "ok"
    return {"status": status, "matured_rows": len(matured), "rolling_mae": round(mae, 4)}


def run_daily(silver: Silver, summary: dict, run_log: RunLog) -> dict:
    champion = summary["champion"]
    model = summary["models"][champion]
    base = {
        "run_id": run_log.run_id,
        "champion": champion,
        "model_name": model["name"],
        "backtest_mae": model["mae"],
        "share_overpriced": summary["vrp"]["share_overpriced"],
        "model_commit": summary["commit"][:8],
    }
    last_price_date = silver.prices.index.max()
    if silver.stale:
        log.warning("Skipping scoring, stale inputs: %s", ", ".join(silver.stale))
        with run_log.step("gold:score") as record:
            record["status"] = "skipped"
        return {**base, "status": "delayed", "date": str(last_price_date.date())}

    with run_log.step("gold:score") as record:
        frame = build_features(silver.prices, silver.indices)
        write_table(frame, "gold", "features_daily")
        today, forecast = forecast_latest(frame, champion)
        row = frame.loc[today]
        metrics = {
            **base,
            "status": "ok",
            "date": str(today.date()),
            "forecast": round(forecast, 2),
            "vxn": round(float(row["vxn"]), 2),
            "vix": round(float(row["vix"]), 2),
            "rv_21": round(float(row["rv_21"]), 2),
            "premium": round(float(row["vxn"]) - forecast, 2),
        }
        new = pd.DataFrame(
            [{"date": metrics["date"], "model": champion, "forecast": forecast, "vxn": row["vxn"]}]
        )
        forecasts = upsert_table(new, "gold", "forecasts", ["date", "model"])
        forecasts = mature_forecasts(forecasts, frame)
        write_table(forecasts, "gold", "forecasts", index=False)
        health = model_health(forecasts[forecasts["model"] == champion], model["mae"])
        metrics["health"] = health["status"]
        if health["status"] == "alert":
            log.warning("ALERT model health: rolling MAE %s", health["rolling_mae"])
        upsert_table(pd.DataFrame([metrics]), "gold", "daily_metrics", ["date"])
        record["rows_in"] = len(frame)
        record["rows_out"] = 1
    log.info("Forecast %s for %s: %.2f (VXN %.2f)", champion, today.date(), forecast, row["vxn"])
    return metrics
