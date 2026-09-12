import os
import re
import random
import asyncio
import urllib.parse
import urllib.request
import logging
from bson.objectid import ObjectId
from aiohttp import web
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pymongo import MongoClient

logging.basicConfig(level=logging.INFO)

# ==========================================
# 1. CONFIGURATION (NEW TOKEN APPLIED)
# ==========================================
API_ID = 39972309
API_HASH = "dd6e47a51f4f934ed21d346f78aae407"
BOT_TOKEN = "8970048357:AAEbxUotyFA34UjF8Xi5ocJURXqXsuSG7YY"
BOT_USERNAME = "BoultFlixMovieBot"

DB_CHANNEL = -1004240578315
LOG_CHANNEL = -1004328720608
ADMINS = [7908289094]

START_PIC = "https://i.ibb.co/PZtMPSKf/boultflix-popcorn-cart.webp"
UPDATES_CHANNEL_URL = "https://t.me/+f-k01NScSxEyNzc1"
SUPPORT_BOT_URL = "https://t.me/BoultFlixSupportBot"

REACTION_EMOJIS = ["🔥", "⚡", "❤️", "🥰", "🎉", "🤩", "👏", "👌", "🕊️", "😍", "💯", "💖", "🍓", "😎", "✨", "🎬", "🏆", "💎", "🚀"]

# Clear Old Webhooks for New Token
try:
    urllib.request.urlopen(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=5)
    print("🧹 Webhook Cleared for New Token!", flush=True)
except Exception:
    pass

# MongoDB Connection (52,899+ Indexed Movies)
MONGO_URI = "mongodb+srv://ab9816892_db_user:anish12345@cluster0.yogzcqw.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = mongo_client["Cluster0"]
files_col = db["Telegram_Files"]
users_col = db["Users"]

app = Client(
    "BoultFlix_Live_New",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ==========================================
# 2. GUARANTEED HTTP LOG SENDER
# ==========================================
def send_telegram_http(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": LOG_CHANNEL,
            "text": text,
            "parse_mode": "HTML"
        }).encode("utf-8")
        req = urllib.request.Request(url, data=data)
        urllib.request.urlopen(req, timeout=5)
        print("📢 Log alert sent via HTTP API!", flush=True)
    except Exception as e:
        print(f"⚠️ HTTP Log Note: {e}", flush=True)

# ==========================================
# 3. RENDER PORT KEEP-ALIVE SERVER
# ==========================================
async def handle_ping(request):
    return web.Response(text="BoultFlix Bot 24/7 Live", status=200)

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
        print(f"🌐 Keep-Alive Web Server active on port {port}", flush=True)
    except Exception as e:
        print(f"⚠️ Web Server Info: {e}", flush=True)

# ==========================================
# 4. HELPER FUNCTIONS
# ==========================================
async def send_reaction(message):
    try:
        await message.react(emoji=random.choice(REACTION_EMOJIS))
    except Exception:
        pass

def db_find_user(user_id):
    try:
        return users_col.find_one({"user_id": user_id})
    except Exception:
        return None

def db_add_user(user_id, name):
    try:
        users_col.insert_one({"user_id": user_id, "name": name})
    except Exception:
        pass

def db_search_movies(query_pattern):
    try:
        return list(files_col.find({"file_name": {"$regex": query_pattern, "$options": "i"}}).limit(10))
    except Exception:
        return []

def db_get_file_by_id(doc_id):
    try:
        return files_col.find_one({"_id": ObjectId(doc_id)})
    except Exception:
        return None

async def log_user(user):
    try:
        existing = await asyncio.to_thread(db_find_user, user.id)
        if not existing:
            await asyncio.to_thread(db_add_user, user.id, user.first_name)
            username_txt = f"@{user.username}" if user.username else "Nᴏɴᴇ"
            log_text = (
                f"#NewUser 🍿\n\n"
                f"👤 <b>Nᴀᴍᴇ:</b> {user.mention}\n"
                f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
                f"🌐 <b>Usᴇʀɴᴀᴍᴇ:</b> {username_txt}\n"
                f"⚡ <b>Sᴛᴀᴛᴜs:</b> Bᴏᴛ Sᴛᴀʀᴛᴇᴅ"
            )
            await asyncio.to_thread(send_telegram_http, log_text)
    except Exception:
        pass

# ==========================================
# 5. /START COMMAND HANDLER
# ==========================================
@app.on_message(filters.private & filters.command("start"))
async def start_handler(client, message):
    user = message.from_user
    print(f"⚡ /start received from: {user.first_name} ({user.id})", flush=True)
    asyncio.create_task(send_reaction(message))
    asyncio.create_task(log_user(user))

    caption = (
        f"Hᴇʏ 🍿 <b>{user.mention}</b> 🥷\n\n"
        f"📍 <b>Wᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ᴡᴏʀʟᴅ's ᴄᴏᴏʟᴇsᴛ sᴇᴀʀᴄʜ ᴇɴɢɪɴᴇ! ⚡</b>\n\n"
        f"Hᴇʀᴇ ʏᴏᴜ ᴄᴀɴ ʀᴇǫᴜᴇsᴛ ᴍᴏᴠɪᴇs & sᴇʀɪᴇs, ᴊᴜsᴛ sᴇɴᴅ ɴᴀᴍᴇ ᴡɪᴛʜ ᴘʀᴏᴘᴇʀ <b>Gᴏᴏɢʟᴇ sᴘᴇʟʟɪɴɢ</b>..!! 🫧🎬"
    )

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔰 Aᴅᴅ Mᴇ Tᴏ Yᴏᴜʀ Gʀᴏᴜᴘ 🔰", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
        [InlineKeyboardButton("📢 Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇﻟ 📢", url=UPDATES_CHANNEL_URL)],
        [InlineKeyboardButton("📑 Hᴇʟᴘ", callback_data="help_menu"), InlineKeyboardButton("ℹ️ Aʙᴏᴜᴛ", callback_data="about_menu")]
    ])

    try:
        await message.reply_photo(photo=START_PIC, caption=caption, reply_markup=buttons)
    except Exception:
        await message.reply_text(text=caption, reply_markup=buttons)

# ==========================================
# 6. MOVIE SEARCH ENGINE (52,899+ MONGODB DATABASE)
# ==========================================
@app.on_message(filters.private & filters.text & ~filters.command(["start", "help", "about"]))
async def search_movie(client, message):
    raw_query = message.text.strip()
    user = message.from_user
    print(f"🔍 Searching movie: '{raw_query}' from {user.first_name}", flush=True)
    asyncio.create_task(send_reaction(message))

    clean_query = re.sub(r"[^\w\s]", " ", raw_query)
    words = [w for w in clean_query.split() if len(w) > 0]
    regex_pattern = ".*".join([re.escape(w) for w in words]) if words else re.escape(raw_query)

    results = await asyncio.to_thread(db_search_movies, regex_pattern)

    if not results:
        google_query_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(raw_query)}"
        no_results_text = (
            f"<b>Sᴏʀʀʏ {user.first_name}</b>, <b>ɴᴏ ғɪʟᴇs ᴡᴇʀᴇ ғᴏᴜɴᴅ ғᴏʀ ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ</b> <code>{raw_query}</code> 🙁\n\n"
            f"<b>Cʜᴇᴄᴋ ʏᴏᴜʀ sᴘᴇʟʟɪɴɢ ɪɴ Gᴏᴏɢʟᴇ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ</b> 😃\n\n"
            f"📝 <b>Mᴏᴠɪᴇ ʀᴇǫᴜᴇsᴛ ғᴏʀᴍᴀᴛ</b> 👇\n\n"
            f"⚜️ <b>E x ᴀ ᴍ ᴘ ʟ ᴇ :</b> <code>Jawan</code> ᴏʀ <code>Jawan 2023</code>\n\n"
            f"📌 <i>Iғ ʏᴏᴜʀ sᴘᴇʟʟɪɴɢ ɪs ᴄᴏʀʀᴇᴄᴛ ᴘʟᴇᴀsᴇ ʀᴇᴘᴏʀᴛ ᴛᴏ ᴏᴜʀ sᴜᴘᴘᴏʀᴛ ᴛᴇᴀᴍ 👇</i>"
        )
        action_buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Cʜᴇᴄᴋ Sᴘᴇʟʟɪɴɢ Oɴ Gᴏᴏɢʟᴇ 🔍", url=google_query_url)],
            [InlineKeyboardButton("🚀 Rᴇᴘᴏʀᴛ Tᴏ Sᴜᴘᴘᴏʀᴛ Tᴇᴀᴍ 🚀", url=SUPPORT_BOT_URL)]
        ])
        await message.reply_text(text=no_results_text, reply_markup=action_buttons, disable_web_page_preview=True)
        return

    # SAFE 24-BYTE BUTTON CALLBACKS
    buttons = []
    for res in results:
        file_name = res.get("file_name", "Download Video")
        doc_id = str(res.get("_id"))
        display_name = (file_name[:38] + "..") if len(file_name) > 40 else file_name
        buttons.append([InlineKeyboardButton(f"📁 {display_name}", callback_data=f"get_{doc_id}")])

    await message.reply_text(
        f"🎯 <b>Rᴇsᴜʟᴛs ғᴏʀ:</b> <code>{raw_query}</code>\n⚡ <b>Fᴏᴜɴᴅ Fɪʟᴇs:</b> <code>{len(results)}</code>",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ==========================================
# 7. CALLBACK HANDLERS (MENUS & FILE DELIVERY)
# ==========================================
@app.on_callback_query()
async def bot_callbacks(client, query: CallbackQuery):
    data = query.data
    await query.answer("Share & Support Us ❤️")

    if data == "home_menu":
        caption = (
            f"Hᴇʏ 🍿 <b>{query.from_user.mention}</b> 🥷\n\n"
            f"📍 <b>Wᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ᴡᴏʀʟᴅ's ᴄᴏᴏʟᴇsᴛ sᴇᴀʀᴄʜ ᴇɴɢɪɴᴇ! ⚡</b>\n\n"
            f"Hᴇʀᴇ ʏᴏᴜ ᴄᴀɴ ʀᴇǫᴜᴇsᴛ ᴍᴏᴠɪᴇs & sᴇʀɪᴇs, ᴊᴜsᴛ sᴇɴᴅ ɴᴀᴍᴇ ᴡɪᴛʜ ᴘʀᴏᴘᴇʀ <b>Gᴏᴏɢʟᴇ sᴘᴇʟʟɪɴɢ</b>..!! 🫧🎬"
        )
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔰 Aᴅᴅ Mᴇ Tᴏ Yᴏᴜʀ Gʀᴏᴜᴘ 🔰", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
            [InlineKeyboardButton("📢 Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇﻟ 📢", url=UPDATES_CHANNEL_URL)],
            [InlineKeyboardButton("📑 Hᴇʟᴘ", callback_data="help_menu"), InlineKeyboardButton("ℹ️ Aʙᴏᴜᴛ", callback_data="about_menu")]
        ])
        try:
            await query.message.edit_caption(caption=caption, reply_markup=buttons)
        except Exception:
            await query.message.edit_text(text=caption, reply_markup=buttons)

    elif data == "help_menu":
        help_text = (
            "✨ <b>𝗛𝗢𝗪 𝗧𝗢 𝗚𝗘𝗧 𝗠𝗢𝗩𝗜𝗘𝗦, 𝗔𝗡𝗜𝗠𝗘, 𝗪𝗘𝗕 𝗦𝗘𝗥𝗜𝗘𝗦, 𝗘𝗧𝗖</b> ✨\n\n"
            "1) Sᴇᴀʀᴄʜ ᴛʜᴇ ᴄᴏʀʀᴇᴄᴛ ɴᴀᴍᴇ ᴏɴ ɢᴏᴏɢʟᴇ ᴀɴᴅ ᴄᴏᴘʏ ɪᴛ\n"
            "2) Pᴀsᴛᴇ ᴛʜᴇ ɴᴀᴍᴇ ɪɴ ᴛʜᴇ ʙᴏᴛ ᴀɴᴅ sᴇɴᴅ ɪᴛ\n\n"
            "📌 <b>Fᴏʀ ᴡᴇʙ-sᴇʀɪᴇs:</b> <code>Series Name S01</code>\n"
            "📌 <b>Fᴏʀ ᴍᴏᴠɪᴇs:</b> <code>Movie Name Year</code> (Ex: Dhurandhar 2019)"
        )
        help_buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Rᴇǫᴜᴇsᴛ Hᴇʀᴇ 🚀", url=SUPPORT_BOT_URL)],
            [InlineKeyboardButton("⇋ Bᴀᴄᴋ ⇋", callback_data="home_menu")]
        ])
        try:
            await query.message.edit_caption(caption=help_text, reply_markup=help_buttons)
        except Exception:
            await query.message.edit_text(text=help_text, reply_markup=help_buttons)

    elif data == "about_menu":
        about_text = (
            "╭─────[ <b>Mʏ Dᴇᴛᴀɪʟs</b> 🫧 ]──────⍟\n"
            f"├⍟ <b>Mʏ Nᴀᴍᴇ :</b> <a href='https://t.me/{BOT_USERNAME}'>Bᴏᴜʟᴛғʟɪx Mᴏᴠɪᴇs 🫧🫶🏼</a>\n"
            f"├⍟ <b>Dᴇᴠᴇʟᴏᴘᴇʀ :</b> <a href='https://t.me/BoultFlix'>Oᴡɴᴇʀ ⚡</a>\n"
            "├⍟ <b>Dᴀᴛᴀʙᴀsᴇ :</b> <a href='https://www.mongodb.com'>Mᴏɴɢᴏ DB (52,899+ Files)</a>\n"
            "├⍟ <b>Bᴏᴛ Sᴇʀᴠᴇʀ :</b> <a href='https://render.com'>Rᴇɴᴅᴇʀ</a>\n"
            "╰───────────────⍟"
        )
        about_buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("‼️ Dɪsᴄʟᴀɪᴍᴇʀ ‼️", callback_data="disclaimer_menu")],
            [InlineKeyboardButton("⇋ Bᴀᴄᴋ ⇋", callback_data="home_menu")]
        ])
        try:
            await query.message.edit_caption(caption=about_text, reply_markup=about_buttons)
        except Exception:
            await query.message.edit_text(text=about_text, reply_markup=about_buttons)

    elif data == "disclaimer_menu":
        disclaimer_text = (
            "ᴛʜɪꜱ ɪꜱ ᴀɴ ᴏᴘᴇɴ ꜱᴏᴜʀᴄᴇ ᴘʀᴏᴊᴇᴄᴛ.\n\n"
            "ᴀʟʟ ᴛʜᴇ ꜰɪʟᴇꜱ ɪɴ ᴛʜɪꜱ ʙᴏᴛ ᴀʀᴇ ꜰʀᴇᴇʟʏ ᴀᴠᴀɪʟᴀʙʟᴇ ᴏɴ ᴛʜᴇ ɪɴᴛᴇʀɴᴇᴛ ᴏʀ ᴘᴏꜱᴛᴇᴅ ʙʏ ꜱᴏᴍᴇʙᴏᴅʏ ᴇʟꜱᴇ."
        )
        disclaimer_buttons = InlineKeyboardMarkup([[InlineKeyboardButton("⇋ Bᴀᴄᴋ ⇋", callback_data="about_menu")]])
        try:
            await query.message.edit_caption(caption=disclaimer_text, reply_markup=disclaimer_buttons)
        except Exception:
            await query.message.edit_text(text=disclaimer_text, reply_markup=disclaimer_buttons)

    elif data.startswith("get_"):
        doc_id = data.split("get_", 1)[1]
        doc = await asyncio.to_thread(db_get_file_by_id, doc_id)
        if doc and doc.get("file_id"):
            try:
                await client.send_cached_media(chat_id=query.from_user.id, file_id=doc["file_id"])
            except Exception as ex:
                print(f"Cached Send Error: {ex}", flush=True)
                await query.answer("❌ File send error!", show_alert=True)
        else:
            await query.answer("❌ File not found in DB!", show_alert=True)

# ==========================================
# 8. MAIN ENTRY POINT
# ==========================================
async def main():
    print("⏳ Starting Web Server...", flush=True)
    await start_web_server()
    print("⏳ Connecting to Telegram with New Token...", flush=True)
    await app.start()
    print("🚀 BoultFlix Bot Started & Polling Telegram Updates 24/7!", flush=True)

    startup_text = (
        f"⚡ <b>Bᴏᴜʟᴛғʟɪx Mᴏᴠɪᴇs Bᴏᴛ Rᴇsᴛᴀʀᴛᴇᴅ!</b> 🚀\n\n"
        f"👤 <b>Dᴇᴠᴇʟᴏᴘᴇʀ:</b> @BoultFlix\n"
        f"🌐 <b>Sᴇʀᴠᴇʀ:</b> Rᴇɴᴅᴇʀ\n"
        f"🟢 <b>Sᴛᴀᴛᴜs:</b> Oɴʟɪɴᴇ & Rᴇᴀᴅʏ"
    )
    await asyncio.to_thread(send_telegram_http, startup_text)

    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
