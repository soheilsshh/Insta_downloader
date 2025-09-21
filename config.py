import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Download Configuration
DOWNLOAD_PATH = 'downloads'
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB in bytes (Telegram's maximum)
