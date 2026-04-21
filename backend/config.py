import os
import logging
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("bergen_rain")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = str(PROJECT_ROOT / "data" / "rain.db")

# Frost API
DEFAULT_STATION_ID = "SN50540"
FROST_CLIENT_ID = os.getenv("CLIENT_ID")
FROST_CLIENT_SECRET = os.getenv("CLIENT_SECRET")
FROST_API_ENDPOINT = os.getenv("FROST_API_ENDPOINT")


def default_date_range(days=365):
    """Return (start_date, end_date) strings for the last N days."""
    end = datetime.now()
    start = end - timedelta(days=days)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
