import os

def get_int(val, default=0):
    try:
        if not val:
            return default
        return int(str(val).strip())
    except:
        return default

def get_list(val, default=None):
    if default is None:
        default = []
    if not val:
        return default
    res = []
    for item in str(val).replace(",", " ").split():
        try:
            res.append(int(item.strip()))
        except:
            continue
    return res if res else default

# Telegram API Credentials
API_ID = get_int(os.environ.get("API_ID"), 39972309)
API_HASH = os.environ.get("API_HASH", "dd6e47a51f4f934ed21d346f78aae407").strip()
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
BOT_USERNAME = os.environ.get("BOT_USERNAME", "").replace("@", "").strip()

# Admin & Channel IDs
ADMINS = get_list(os.environ.get("ADMINS"), [7067885693])
CHANNELS = get_list(os.environ.get("CHANNELS"), [-1004240578315])
FORCE_SUB_CHANNEL = os.environ.get("FORCE_SUB_CHANNEL", "-1004240578315").strip()
UPDATE_CHANNEL = get_int(os.environ.get("UPDATE_CHANNEL"), -1004240578315)
LOG_CHANNEL = get_int(os.environ.get("LOG_CHANNEL"), -1004240578315)

# Database Configuration
DATABASE_URI = os.environ.get("DATABASE_URI_1", os.environ.get("DATABASE_URI", "")).strip()
DATABASE_URI_1 = DATABASE_URI
DATABASE_NAME = os.environ.get("DATABASE_NAME", "Cluster0").strip()
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "Telegram_Files").strip()

# Search & Filter Settings
MAX_RESULTS = get_int(os.environ.get("MAX_RESULTS"), 10)
MAX_BTN = get_int(os.environ.get("MAX_BTN"), 10)
CACHE_TIME = get_int(os.environ.get("CACHE_TIME"), 300)

# TMDb & Auto-Post
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "c357c290aea604400f0d2b8e198db943").strip()
AUTO_POST = str(os.environ.get("AUTO_POST", "True")).lower() == "true"

# Shortlink Settings
USE_SHORTLINK = str(os.environ.get("USE_SHORTLINK", "False")).lower() == "true"
SHORTLINK_URL = os.environ.get("SHORTLINK_URL", "gplinks.com").strip()
SHORTLINK_API = os.environ.get("SHORTLINK_API", "").strip()
VERIFY_EXPIRE = get_int(os.environ.get("VERIFY_EXPIRE"), 86400)

# Web Server Port
PORT = get_int(os.environ.get("PORT"), 8080)
