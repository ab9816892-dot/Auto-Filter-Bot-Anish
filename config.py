import os

# Telegram API Credentials
API_ID = int(os.environ.get("API_ID", "39972309"))
API_HASH = os.environ.get("API_HASH", "dd6e47a51f4f934ed21d346f78aae407")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "").replace("@", "")

# Admin & Channel IDs
ADMINS = [int(admin) for admin in os.environ.get("ADMINS", "7067885693").split()]
CHANNELS = [int(ch) for ch in os.environ.get("CHANNELS", "-1004240578315").split()]
FORCE_SUB_CHANNEL = os.environ.get("FORCE_SUB_CHANNEL", "-1004240578315")
UPDATE_CHANNEL = int(os.environ.get("UPDATE_CHANNEL", "-1004240578315"))
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "-1004240578315"))

# Database (Both aliases supported)
DATABASE_URI = os.environ.get("DATABASE_URI_1", os.environ.get("DATABASE_URI", ""))
DATABASE_URI_1 = DATABASE_URI
DATABASE_NAME = os.environ.get("DATABASE_NAME", "Cluster0")

# TMDb & Auto-Post
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "c357c290aea604400f0d2b8e198db943")
AUTO_POST = os.environ.get("AUTO_POST", "True").lower() == "true"

# Shortlink Settings
USE_SHORTLINK = os.environ.get("USE_SHORTLINK", "False").lower() == "true"
SHORTLINK_URL = os.environ.get("SHORTLINK_URL", "gplinks.com")
SHORTLINK_API = os.environ.get("SHORTLINK_API", "")
