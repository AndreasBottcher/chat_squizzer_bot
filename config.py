import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")
DB_PATH = Path(os.getenv("DB_PATH", "messages.db"))
LOG_LEVEL = os.getenv("LOG_LEVEL", logging.INFO)

DATETIME_FORMAT = os.getenv(
    "DATETIME_FORMAT", "%d.%m.%Y %H:%M:%S"
)  # unused at the moment
DATETIME_FORMAT_SHORT = os.getenv("DATETIME_FORMAT_SHORT", "%d.%m.%Y %H:%M")
TOP_USERS_COUNT = int(os.getenv("TOP_USERS_COUNT", "3"))
TOP_NOUNS_COUNT = int(os.getenv("TOP_NOUNS_COUNT", "5"))
SUMMARY_PERIOD_HOURS = int(os.getenv("SUMMARY_PERIOD_HOURS", "24"))

# NLTK data directory
NLTK_DATA_DIR = Path(os.getenv("NLTK_DATA_DIR", "nltk_data")).resolve()
NLTK_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Get logger instance
logger = logging.getLogger(__name__)
