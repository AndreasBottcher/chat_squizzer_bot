import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

LOG_LEVEL = os.getenv('LOG_LEVEL', logging.INFO)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

DATETIME_FORMAT = os.getenv('DATETIME_FORMAT', '%d.%m.%Y %H:%M:%S')

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Get logger instance
logger = logging.getLogger(__name__)
