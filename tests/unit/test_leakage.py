import numpy as np
import pandas as pd

from qvol.features.build import FEATURES, build_features


def test_changing_the_future_does_not_change_todays_features(market):
    prices, indices = market
    cutoff = prices.index[300]
    baseline = build_features(prices, indices)

    rng = np.random.default_rng(1)
    future = prices.index > cutoff
    shocked_prices = prices.copy()
    shocked_prices.loc[future, "adj_close"] *= rng.uniform(0.5, 1.5, future.sum())
    shocked_indices = indices.copy()
    shocked_indices.loc[future] = rng.uniform(50, 100, (future.sum(), indices.shape[1]))

    shocked = build_features(shocked_prices, shocked_indices)
    pd.testing.assert_frame_equal(baseline.loc[:cutoff, FEATURES], shocked.loc[:cutoff, FEATURES])
    assert baseline.loc[cutoff, "y"] != shocked.loc[cutoff, "y"]
