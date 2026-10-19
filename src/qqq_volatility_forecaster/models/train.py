from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer
from xgboost import XGBRegressor

from qqq_volatility_forecaster.config import FIRST_TEST_YEAR, HORIZON, SEED
from qqq_volatility_forecaster.features.build import FEATURES, TARGET
from qqq_volatility_forecaster.models.baselines import ColumnForecast
from qqq_volatility_forecaster.models.walk_forward import walk_forward_splits

HAR_COLUMNS = ["rv_5", "rv_21", "rv_63", "vxn"]


@dataclass(frozen=True)
class ModelSpec:
    name: str
    columns: list[str]
    make: Callable[[], object]


MODELS: dict[str, ModelSpec] = {
    "M0": ModelSpec("Naive: last month repeats", ["rv_21"], lambda: ColumnForecast("rv_21")),
    "M1": ModelSpec("Market: VXN", ["vxn"], lambda: ColumnForecast("vxn")),
    "M2": ModelSpec(
        "Linear regression (HAR)",
        HAR_COLUMNS,
        lambda: make_pipeline(FunctionTransformer(np.log), LinearRegression()),
    ),
    "M3": ModelSpec(
        "Random forest",
        FEATURES,
        lambda: RandomForestRegressor(
            n_estimators=300, max_depth=6, min_samples_leaf=20, random_state=SEED, n_jobs=-1
        ),
    ),
    "M4": ModelSpec(
        "XGBoost",
        FEATURES,
        lambda: XGBRegressor(
            n_estimators=300,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.8,
            random_state=SEED,
            n_jobs=1,
        ),
    ),
}


def backtest(
    frame: pd.DataFrame,
    models: dict[str, ModelSpec] = MODELS,
    first_test_year: int = FIRST_TEST_YEAR,
    gap: int = HORIZON,
) -> pd.DataFrame:
    usable = frame[FEATURES + [TARGET]].notna().all(axis=1).to_numpy()
    results = []
    for year, train_idx, test_idx in walk_forward_splits(frame.index, first_test_year, gap):
        train = frame.iloc[train_idx[usable[train_idx]]]
        test = frame.iloc[test_idx[usable[test_idx]]]
        if train.empty or test.empty:
            continue
        for model_id, spec in models.items():
            model = spec.make().fit(train[spec.columns], np.log(train[TARGET]))
            results.append(
                pd.DataFrame(
                    {
                        "date": test.index,
                        "year": year,
                        "model": model_id,
                        "forecast": np.exp(model.predict(test[spec.columns])),
                        "actual": test[TARGET].to_numpy(),
                        "vxn": test["vxn"].to_numpy(),
                        "train_rows": len(train),
                    }
                )
            )
    return pd.concat(results, ignore_index=True)
