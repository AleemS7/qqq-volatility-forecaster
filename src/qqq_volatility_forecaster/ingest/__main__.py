import logging

import pandas as pd

from qqq_volatility_forecaster import config
from qqq_volatility_forecaster.ingest.fred import fetch_series
from qqq_volatility_forecaster.ingest.yahoo import fetch_prices
from qqq_volatility_forecaster.io.tables import write_table

log = logging.getLogger(__name__)


def main() -> None:
    prices = fetch_prices(config.TICKER, config.PRICE_START)
    indices = pd.concat(
        [fetch_series(config.VXN_SERIES), fetch_series(config.VIX_SERIES)], axis=1, sort=True
    )
    write_table(prices, "qqq_prices")
    write_table(indices, "vol_indices")
    log.info(
        "Ingested %d price rows (%s to %s) and %d index rows",
        len(prices),
        prices.index.min().date(),
        prices.index.max().date(),
        len(indices),
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format=config.LOG_FORMAT)
    main()
