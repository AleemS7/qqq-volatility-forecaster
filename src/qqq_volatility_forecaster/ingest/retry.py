import logging

from tenacity import before_sleep_log, retry, stop_after_attempt, wait_exponential

log = logging.getLogger(__name__)

MAX_ATTEMPTS = 4

with_retries = retry(
    stop=stop_after_attempt(MAX_ATTEMPTS),
    wait=wait_exponential(multiplier=2, min=2, max=16),
    before_sleep=before_sleep_log(log, logging.WARNING),
    reraise=True,
)
