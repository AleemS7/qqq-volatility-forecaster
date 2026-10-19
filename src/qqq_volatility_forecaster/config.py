from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"

TICKER = "QQQ"
PRICE_START = "1999-03-10"
VXN_SERIES = "VXNCLS"
VIX_SERIES = "VIXCLS"

TRADING_DAYS = 252
HORIZON = 21

FIRST_TRAIN_YEAR = 2001
FIRST_TEST_YEAR = 2007

CHAMPION_MIN_BEAT_SHARE = 0.6
SEED = 42

BRIEF_MODEL = "claude-opus-5-5"
BRIEF_PROMPT_VERSION = "brief_v1"
BRIEF_MAX_ATTEMPTS = 2

LOG_FORMAT = "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
