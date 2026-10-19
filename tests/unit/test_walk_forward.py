import pandas as pd

from qvol.models.walk_forward import walk_forward_splits

DATES = pd.bdate_range("2001-01-01", "2010-12-31")


def test_one_fold_per_test_year():
    years = [year for year, _, _ in walk_forward_splits(DATES, 2007)]
    assert years == [2007, 2008, 2009, 2010]


def test_test_rows_cover_exactly_that_year():
    for year, _, test in walk_forward_splits(DATES, 2007):
        assert (DATES[test].year == year).all()
        assert (DATES.year == year).sum() == len(test)


def test_no_training_target_window_reaches_the_test_year():
    gap = 21
    for _, train, test in walk_forward_splits(DATES, 2007, gap):
        assert train.max() + gap < test.min()
        assert test.min() - train.max() == gap + 1


def test_training_window_expands():
    sizes = [len(train) for _, train, _ in walk_forward_splits(DATES, 2007)]
    assert sizes == sorted(sizes)
    assert all(train[0] == 0 for _, train, _ in walk_forward_splits(DATES, 2007))
