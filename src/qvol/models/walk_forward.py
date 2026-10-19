from collections.abc import Iterator

import numpy as np
import pandas as pd

from qvol.config import HORIZON


def walk_forward_splits(
    dates: pd.DatetimeIndex, first_test_year: int, gap: int = HORIZON
) -> Iterator[tuple[int, np.ndarray, np.ndarray]]:
    years = dates.year
    for year in sorted(set(years[years >= first_test_year])):
        test = np.flatnonzero(years == year)
        train = np.arange(max(test[0] - gap, 0))
        yield year, train, test
