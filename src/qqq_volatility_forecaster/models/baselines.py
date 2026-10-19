import numpy as np
import pandas as pd


class ColumnForecast:
    def __init__(self, column: str):
        self.column = column

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "ColumnForecast":
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return np.log(X[self.column].to_numpy())
