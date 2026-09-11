import os
import re

# Telegram API Setup
API_ID = int(os.environ.get("API_ID", "39972309"))
API_HASH = os.environ.get("API_HASH", "dd6e47a51f4f934ed21d346f78aae407")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "")
ADMINS = [int(admin) for admin in os.environ.get("ADMINS", "").split() if admin]

# Database & Channel Configuration
DATABASE_URI = os.environ.get("DATABASE_URI", "mongodb+srv://ab9816892_db_user:Fdohpq7hpwb7wLrW@cluster0.yogzcqw.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "Cluster0")
CHANNELS = [int(ch) for ch in os.environ.get("CHANNELS", "-1004240578315").split() if ch]
UPDATE_CHANNEL = int(os.environ.get("UPDATE_CHANNEL", "-1004240578315"))
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "0"))

# TMDb Metadata Integration
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "c357c290aea604400f0d2b8e198db943")
AUTO_POST = os.environ.get("AUTO_POST", "True").lower() == "true"

# 24-Hour Shortlink Token System
USE_SHORTLINK = os.environ.get("USE_SHORTLINK", "False").lower() == "true"
SHORTLINK_URL = os.environ.get("SHORTLINK_URL", "shareus.io")
SHORTLINK_API = os.environ.get("SHORTLINK_API", "")
VERIFY_EXPIRE = int(os.environ.get("VERIFY_EXPIRE", 86400))  # 86400 sec = 24 Hours

# Universal Custom File Caption
CUSTOM_FILE_CAPTION = os.environ.get(
    "CUSTOM_FILE_CAPTION",
    """🎬 **{file_name}**

📦 **Size :** `{file_size}`
🎧 **Audio :** Multi / Dual Audio
🌟 **Channel :** @{bot_username}"""
)

MAX_RESULTS = int(os.environ.get("MAX_RESULTS", 10))
