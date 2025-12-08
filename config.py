import logging
from os import getenv
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Environment variables
BOT_TOKEN = getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")
DB_PATH = Path(getenv("DB_PATH", "messages.db"))
LOG_LEVEL = getenv("LOG_LEVEL", logging.INFO)

DATETIME_FORMAT = getenv("DATETIME_FORMAT", "%d.%m.%Y %H:%M:%S")  # unused at the moment
DATETIME_FORMAT_SHORT = getenv("DATETIME_FORMAT_SHORT", "%d.%m.%Y %H:%M")
TOP_USERS_COUNT = int(getenv("TOP_USERS_COUNT", "3"))
TOP_NOUNS_COUNT = int(getenv("TOP_NOUNS_COUNT", "5"))
SUMMARY_PERIOD_HOURS = int(getenv("SUMMARY_PERIOD_HOURS", "24"))

# NLTK data directory
NLTK_DATA_DIR = Path(getenv("NLTK_DATA_DIR", "nltk_data")).resolve()
NLTK_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Get logger instance
logger = logging.getLogger(__name__)
