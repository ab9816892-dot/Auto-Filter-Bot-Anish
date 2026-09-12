import os
import re
import time
import random
import asyncio
import urllib.parse
import logging
from bson.objectid import ObjectId
from aiohttp import web
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pymongo import MongoClient

logging.basicConfig(level=logging.INFO)

# ==========================================
# 1. CONFIGURATION (RENDER ENV VARIABLES)
# ==========================================
API_ID = int(os.environ.get("API_ID", "39972309"))
API_HASH = os.environ.get("API_HASH", "dd6e47a51f4f934ed21d346f78aae407")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8970048357:AAEbxUotyFA34UjF8Xi5ocJURXqXsuSG7YY")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "BoultFlixMovieBot")

DB_CHANNEL = int(os.environ.get("CHANNELS", "-1004240578315"))
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "-1004328720608"))
ADMINS = [int(x) for x in os.environ.get("ADMINS", "7819476449").split(",")]

USE_SHORTLINK = os.environ.get("USE_SHORTLINK", "True").lower() == "true"
SHORTLINK_URL = os.environ.get("SHORTLINK_URL", "gplinks.com")
SHORTLINK_API = os.environ.get("SHORTLINK_API", "875b05e0ce2632b7f8b29953b12571dbb5a61604")

START_PIC = "https://i.ibb.co/PZtMPSKf/boultflix-popcorn-cart.webp"
UPDATES_CHANNEL_URL = "https://t.me/+f-k01NScSxEyNzc1"
SUPPORT_BOT_URL = "https://t.me/BoultFlixSupportBot"

REACTION_EMOJIS = [
    "🔥", "⚡", "❤️", "🍿", "🥰", "🎉", "🤩", "👏", 
    "👌", "🕊️", "😍", "💯", "💖", "🍓", "🍾", "😎", 
    "👾", "✨", "🤙", "🥂", "🎬", "🏆", "💎", "👻", 
    "🚀", "👑", "🫡", "🤝", "💫", "🌟"
]

# MongoDB Connection
MONGO_URI = os.environ.get("DATABASE_URI_1", "mongodb+srv://ab9816892_db_user:anish12345@cluster0.yogzcqw.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = mongo_client[os.environ.get("DATABASE_NAME", "Cluster0")]
files_col = db["telegram_files"]
users_col = db["users"]

app = Client(
    "BoultFlix_Rpeditz_Production",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ==========================================
# 2. RENDER KEEP-ALIVE SERVER
# ==========================================
async def handle_ping(request):
    return web.Response(text="BoultFlix Bot is Live 24/7!", status=200)

async def start_web_server():
    server = web.Application()
    server.router.add_get("/", handle_ping)
    server.router.add_get("/health", handle_ping)
    runner = web.AppRunner(server)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    try:
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        print(f"🌐 Keep-Alive Server active on port {port}", flush=True)
    except Exception as e:
        print(f"⚠️ Port Info: {e}", flush=True)

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
async def send_reaction(message):
    try:
        await message.react(emoji=random.choice(REACTION_EMOJIS))
    except Exception:
        pass

def format_size(size_in_bytes):
    if not size_in_bytes:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} GB"

def db_add_user(user_id):
    try:
        if not users_col.find_one({"_id": user_id}):
            users_col.insert_one({"_id": user_id})
    except Exception:
        pass

def db_search_movies(query_pattern, skip=0, limit=10):
    try:
        cursor = files_col.find({"file_name": {"$regex": query_pattern, "$options": "i"}}).skip(skip).limit(limit)
        results = list(cursor)
        total = files_col.count_documents({"file_name": {"$regex": query_pattern, "$options": "i"}})
        return results, total
    except Exception as e:
        print(f"DB Search Error: {e}", flush=True)
        return [], 0

def db_get_file_by_id(doc_id):
    try:
        return files_col.find_one({"_id": ObjectId(doc_id)})
    except Exception:
        return None

# ==========================================
# 4. /START HANDLER & FILE DELIVERY
# ==========================================
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    asyncio.create_task(send_reaction(message))
    user = message.from_user
    db_add_user(user.id)

    if len(message.command) > 1 and message.command[1].startswith("file_"):
        doc_id = message.command[1].replace("file_", "")
        doc = await asyncio.to_thread(db_get_file_by_id, doc_id)
        if doc:
            file_btn = InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Fast download / Watch online 🖥️", callback_data=f"dl_{doc_id}")],
                [InlineKeyboardButton("ℹ️ View audio & subs info ℹ️", callback_data=f"info_{doc_id}")],
                [InlineKeyboardButton("📌 Join updates channel 📌", url=UPDATES_CHANNEL_URL)]
            ])
            try:
                chat_id_src = doc.get("chat_id", DB_CHANNEL)
                msg_id_src = doc.get("message_id")
                
                if msg_id_src:
                    await client.copy_message(
                        chat_id=user.id,
                        from_chat_id=chat_id_src,
                        message_id=msg_id_src,
                        reply_markup=file_btn
                    )
                elif doc.get("file_id"):
                    await client.send_cached_media(
                        chat_id=user.id,
                        file_id=doc["file_id"],
                        reply_markup=file_btn
                    )
                return
            except Exception as e:
                print(f"File Delivery Error: {e}", flush=True)
                # Fallback to direct file_id send if copy_message fails
                try:
                    if doc.get("file_id"):
                        await client.send_cached_media(chat_id=user.id, file_id=doc["file_id"], reply_markup=file_btn)
                        return
                except Exception:
                    pass
                await message.reply_text("❌ File send error! Please try again.")
                return

    caption = (
        f"Hey 🍿 <b>{user.first_name}</b> 🥷\n\n"
        f"📍 <b>Welcome to the world's coolest search engine! ⚡</b>\n\n"
        f"Here you can request movies & series, just send name with proper Google spelling..!! 🫧🎬"
    )
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔰 Add me to your group 🔰", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
        [InlineKeyboardButton("📢 Updates channel 📢", url=UPDATES_CHANNEL_URL)],
        [InlineKeyboardButton("📑 Help", callback_data="help_menu"), InlineKeyboardButton("ℹ️ About", callback_data="about_menu")]
    ])
    
    try:
        await message.reply_photo(photo=START_PIC, caption=caption, reply_markup=buttons)
    except Exception:
        await message.reply_text(text=caption, reply_markup=buttons)

# ==========================================
# 5. RPEDITZ STYLE MOVIE SEARCH ENGINE
# ==========================================
@app.on_message(filters.text & filters.private & ~filters.command(["start", "help", "about"]))
async def search_movie(client, message):
    start_time = time.time()
    asyncio.create_task(send_reaction(message))

    raw_query = message.text.strip()
    user = message.from_user

    clean_query = re.sub(r"[^\w\s]", " ", raw_query)
    words = [w for w in clean_query.split() if len(w) > 0]
    regex_pattern = ".*".join([re.escape(w) for w in words]) if words else re.escape(raw_query)

    results, total = await asyncio.to_thread(db_search_movies, regex_pattern, 0, 10)
    time_taken = f"{time.time() - start_time:.2f}"

    if not results:
        google_query_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(raw_query)}"
        no_results_text = (
            f"<b>Sorry {user.first_name}</b>, <b>no files were found for your request</b> <code>{raw_query}</code> 🙁\n\n"
            f"<b>Check your spelling in Google and try again</b> 😃\n\n"
            f"📝 <b>Movie request format</b> 👇\n\n"
            f"⚜️ <b>Example :</b> <code>Jawan</code> or <code>Jawan 2023</code>\n\n"
            f"📝 <b>Series request format</b> 👇\n\n"
            f"⚜️ <b>Example :</b> <code>Loki S01</code> or <code>Loki S01E04</code> or <code>Lucifer S03E24</code>\n\n"
            f"🚯 <b>Don't use ➡️</b> <code>':( ! , . /)</code>\n\n"
            f"📌 <i>If your spelling and format is correct then please report to our support team 👇</i>"
        )
        action_buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Check spelling on Google 🔍", url=google_query_url)],
            [InlineKeyboardButton("🚀 Report to support team 🚀", url=SUPPORT_BOT_URL)]
        ])
        await message.reply_text(text=no_results_text, reply_markup=action_buttons, disable_web_page_preview=True)
        return

    res_text = (
        f"<b>Title :</b> <code>{raw_query}</code>\n"
        f"📁 <b>Total files :</b> <code>{total}</code>\n"
        f"⏳ <b>Result in :</b> <code>{time_taken} seconds</code>\n\n"
        f"🧃 <b>Requested by :</b> {user.mention}\n"
        f"⚜️ <b>Powered by :</b> <a href='https://t.me/{BOT_USERNAME}'>HD Pro Search Bot</a> ⚡\n\n"
        f"<b><u>Your requested files are here</u></b>\n\n"
    )

    for idx, doc in enumerate(results, start=1):
        doc_id = str(doc.get("_id"))
        f_name = doc.get("file_name", "Movie File")
        f_size = format_size(doc.get("file_size", 0))
        link = f"https://t.me/{BOT_USERNAME}?start=file_{doc_id}"
        res_text += f"{idx}. <a href='{link}'>[{f_size}] {f_name}</a>\n\n"

    rpeditz_buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("Remove ads", callback_data="remove_ads"), InlineKeyboardButton("Send all", callback_data="send_all")],
        [
            InlineKeyboardButton("Quality", callback_data="filter_quality"),
            InlineKeyboardButton("Language", callback_data="filter_language"),
            InlineKeyboardButton("Season", callback_data="filter_season")
        ],
        [
            InlineKeyboardButton("Page", callback_data="ignore"),
            InlineKeyboardButton("1/1", callback_data="ignore"),
            InlineKeyboardButton("Next ➢", callback_data="ignore")
        ],
        [InlineKeyboardButton("« No more pages available »", callback_data="ignore")]
    ])

    await message.reply_text(
        text=res_text,
        reply_markup=rpeditz_buttons,
        disable_web_page_preview=True
    )

# ==========================================
# 6. CALLBACK HANDLERS
# ==========================================
@app.on_callback_query()
async def bot_callbacks(client, query: CallbackQuery):
    data = query.data

    if data == "home_menu":
        await query.answer("Share & Support Us ❤️")
        caption = (
            f"Hey 🍿 <b>{query.from_user.first_name}</b> 🥷\n\n"
            f"📍 <b>Welcome to the world's coolest search engine! ⚡</b>\n\n"
            f"Here you can request movies & series, just send name with proper Google spelling..!! 🫧🎬"
        )
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔰 Add me to your group 🔰", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
            [InlineKeyboardButton("📢 Updates channel 📢", url=UPDATES_CHANNEL_URL)],
            [InlineKeyboardButton("📑 Help", callback_data="help_menu"), InlineKeyboardButton("ℹ️ About", callback_data="about_menu")]
        ])
        try:
            await query.message.edit_caption(caption=caption, reply_markup=buttons)
        except Exception:
            await query.message.edit_text(text=caption, reply_markup=buttons)

    elif data == "help_menu":
        await query.answer("Help Menu")
        help_text = (
            "✨ <b>HOW TO GET MOVIES, ANIME, WEB SERIES, ETC</b> ✨\n\n"
            "1) Search the correct name on google and copy it\n"
            "2) Paste the name in the bot and send it\n\n"
            "📌 <b>For web-series:</b> Series Name S01\n"
            "📌 <b>For movies:</b> Movie Name Year (Ex: Dhurandhar 2019)"
        )
        help_buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Request here 🚀", url=SUPPORT_BOT_URL)],
            [InlineKeyboardButton("⇋ Back ⇋", callback_data="home_menu")]
        ])
        try:
            await query.message.edit_caption(caption=help_text, reply_markup=help_buttons)
        except Exception:
            await query.message.edit_text(text=help_text, reply_markup=help_buttons)

    elif data == "about_menu":
        await query.answer("About Details")
        about_text = (
            "╭─────[ <b>My details</b> 🫧 ]──────⍟\n"
            f"├⍟ <b>My name :</b> <a href='https://t.me/{BOT_USERNAME}'>BoultFlix Movies 🫧🫶🏼</a>\n"
            f"├⍟ <b>Developer :</b> <a href='https://t.me/BoultFlix'>Owner ⚡</a>\n"
            "├⍟ <b>Database :</b> <a href='https://www.mongodb.com'>Mongo DB (52,899+ Files)</a>\n"
            "├⍟ <b>Bot server :</b> <a href='https://render.com'>Render</a>\n"
            "╰───────────────⍟"
        )
        about_buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("‼️ Disclaimer ‼️", callback_data="disclaimer_menu")],
            [InlineKeyboardButton("⇋ Back ⇋", callback_data="home_menu")]
        ])
        try:
            await query.message.edit_caption(caption=about_text, reply_markup=about_buttons)
        except Exception:
            await query.message.edit_text(text=about_text, reply_markup=about_buttons)

    elif data == "disclaimer_menu":
        await query.answer("Disclaimer")
        disclaimer_text = (
            "This is an open source project.\n\n"
            "All the files in this bot are freely available on the internet or posted by somebody else. "
            "Just for easy searching this bot is indexing files which are already uploaded on telegram."
        )
        disclaimer_buttons = InlineKeyboardMarkup([[InlineKeyboardButton("⇋ Back ⇋", callback_data="about_menu")]])
        try:
            await query.message.edit_caption(caption=disclaimer_text, reply_markup=disclaimer_buttons)
        except Exception:
            await query.message.edit_text(text=disclaimer_text, reply_markup=disclaimer_buttons)

    elif data == "filter_quality":
        await query.answer("Select Quality")
        q_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("360p", callback_data="ignore"), InlineKeyboardButton("480p", callback_data="ignore")],
            [InlineKeyboardButton("720p", callback_data="ignore"), InlineKeyboardButton("1080p", callback_data="ignore")],
            [InlineKeyboardButton("1440p", callback_data="ignore"), InlineKeyboardButton("2160p", callback_data="ignore")],
            [InlineKeyboardButton("4K", callback_data="ignore")],
            [InlineKeyboardButton("« Back to files »", callback_data="home_menu")]
        ])
        try:
            await query.message.edit_text("⚙️ <b>Select quality 👇</b>", reply_markup=q_markup)
        except Exception:
            pass

    elif data == "filter_language":
        await query.answer("Select Language")
        l_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Malayalam", callback_data="ignore"), InlineKeyboardButton("Tamil", callback_data="ignore")],
            [InlineKeyboardButton("English", callback_data="ignore"), InlineKeyboardButton("Hindi", callback_data="ignore")],
            [InlineKeyboardButton("Telugu", callback_data="ignore"), InlineKeyboardButton("Kannada", callback_data="ignore")],
            [InlineKeyboardButton("Gujarati", callback_data="ignore"), InlineKeyboardButton("Marathi", callback_data="ignore")],
            [InlineKeyboardButton("Punjabi", callback_data="ignore"), InlineKeyboardButton("Dual Audio", callback_data="ignore")],
            [InlineKeyboardButton("« Back to files »", callback_data="home_menu")]
        ])
        try:
            await query.message.edit_text("🌐 <b>Select language 👇</b>", reply_markup=l_markup)
        except Exception:
            pass

    elif data == "filter_season":
        await query.answer("Select Season")
        s_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Season 1", callback_data="ignore"), InlineKeyboardButton("Season 2", callback_data="ignore")],
            [InlineKeyboardButton("Season 3", callback_data="ignore"), InlineKeyboardButton("Season 4", callback_data="ignore")],
            [InlineKeyboardButton("Season 5", callback_data="ignore"), InlineKeyboardButton("Season 6", callback_data="ignore")],
            [InlineKeyboardButton("« Back to files »", callback_data="home_menu")]
        ])
        try:
            await query.message.edit_text("🎬 <b>Select season 👇</b>", reply_markup=s_markup)
        except Exception:
            pass

    elif data.startswith("dl_"):
        await query.answer("Preparing shortlink verification...", show_alert=False)
        doc_id = data.replace("dl_", "")
        short_link = f"https://{SHORTLINK_URL}/api?api={SHORTLINK_API}&url=https://t.me/{BOT_USERNAME}?start=file_{doc_id}"
        dl_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Fast download / Watch online 🖥️", url=short_link)],
            [InlineKeyboardButton("📌 Join updates channel 📌", url=UPDATES_CHANNEL_URL)]
        ])
        await query.message.reply_text("✨ <b>Click below to complete verification and get your file:</b>", reply_markup=dl_markup)

    elif data.startswith("info_"):
        await query.answer("Audio & Subs Details: Hindi Audio, English Subtitles (1080p Web-DL).", show_alert=True)

    elif data in ["remove_ads", "send_all", "ignore"]:
        await query.answer("⚡ Action executed successfully!", show_alert=False)

# ==========================================
# 7. MAIN ENTRY POINT
# ==========================================
async def main():
    await start_web_server()
    await app.start()
    print("🚀 BoultFlix Bot Started & Polling Telegram Updates 24/7!", flush=True)
    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
