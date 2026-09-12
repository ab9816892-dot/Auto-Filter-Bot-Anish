import os
import re
import random
import asyncio
import urllib.parse
import logging
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pymongo import MongoClient

logging.basicConfig(level=logging.INFO)

# ==========================================
# 1. CONFIGURATION (ACCURATE IDS)
# ==========================================
API_ID = 39972309
API_HASH = "dd6e47a51f4f934ed21d346f78aae407"
BOT_TOKEN = "8520883339:AAG-ZmU0e2FiehtEoiZtLuCl852bVMydgVE"
BOT_USERNAME = "BoultFlixMovieBot"

# Exact Channels & Admins
DB_CHANNEL = -1004240578315
LOG_CHANNEL = -1004328720608
ADMINS = [7908289094]

START_PIC = "https://i.ibb.co/PZtMPSKf/boultflix-popcorn-cart.webp"
UPDATES_CHANNEL_URL = "https://t.me/+f-k01NScSxEyNzc1"
SUPPORT_BOT_URL = "https://t.me/BoultFlixSupportBot"

# 100% Valid Telegram Supported Reaction Emojis
REACTION_EMOJIS = [
    "🔥", "⚡", "❤️", "🥰", "🎉", "🤩", "👏", 
    "👌", "🕊️", "😍", "💯", "💖", "🍓", "🍾", "😎", 
    "👾", "✨", "🎬", "🏆", "💎", "👻", "🚀", "👑"
]

# MongoDB Connection
MONGO_URI = "mongodb+srv://ab9816892_db_user:anish12345@cluster0.yogzcqw.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

mongo_client = None
files_col = None
users_col = None

try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = mongo_client["Cluster0"]
    files_col = db["Telegram_Files"]
    users_col = db["Users"]
    print("✅ MongoDB Connected Successfully!")
except Exception as e:
    print(f"⚠️ MongoDB Connection Warning: {e}")

app = Client(
    "BoultFlixMovieBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ==========================================
# 2. RENDER PORT KEEP-ALIVE SERVER
# ==========================================
async def handle_http(reader, writer):
    res = "HTTP/1.1 200 OK\r\nContent-Length: 14\r\n\r\nBoultFlix Live"
    writer.write(res.encode("utf-8"))
    await writer.drain()
    writer.close()

async def start_web_server():
    port = int(os.environ.get("PORT", 8080))
    try:
        await asyncio.start_server(handle_http, "0.0.0.0", port)
        print(f"🌐 Keep-Alive Web Server active on port {port}")
    except Exception:
        pass

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
async def send_reaction(message):
    try:
        await message.react(emoji=random.choice(REACTION_EMOJIS))
    except Exception:
        pass

def db_find_user(user_id):
    if users_col is not None:
        return users_col.find_one({"user_id": user_id})
    return None

def db_add_user(user_id, name):
    if users_col is not None:
        users_col.insert_one({"user_id": user_id, "name": name})

def db_search_movies(query_pattern):
    if files_col is not None:
        return list(files_col.find({"file_name": {"$regex": query_pattern, "$options": "i"}}).limit(10))
    return []

def db_save_new_file(media, msg_id, caption_text):
    if files_col is not None:
        fname = getattr(media, "file_name", None) or f"Video_{msg_id}.mp4"
        files_col.update_one(
            {"file_id": media.file_id},
            {"$set": {
                "file_id": media.file_id,
                "file_name": fname,
                "file_size": media.file_size,
                "chat_id": DB_CHANNEL,
                "message_id": msg_id,
                "caption": caption_text
            }},
            upsert=True
        )

async def log_user(user):
    try:
        existing = await asyncio.to_thread(db_find_user, user.id)
        if not existing:
            await asyncio.to_thread(db_add_user, user.id, user.first_name)
            if LOG_CHANNEL:
                username_txt = f"@{user.username}" if user.username else "Nᴏɴᴇ"
                log_text = (
                    f"#NewUser 🍿\n\n"
                    f"👤 <b>Nᴀᴍᴇ:</b> {user.mention}\n"
                    f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
                    f"🌐 <b>Usᴇʀɴᴀᴍᴇ:</b> {username_txt}\n"
                    f"⚡ <b>Sᴛᴀᴛᴜs:</b> Bᴏᴛ Sᴛᴀʀᴛᴇᴅ"
                )
                await app.send_message(LOG_CHANNEL, log_text)
    except Exception as e:
        print(f"⚠️ Log User Error: {e}")

# ==========================================
# 4. /START HANDLER
# ==========================================
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    asyncio.create_task(send_reaction(message))
    user = message.from_user
    asyncio.create_task(log_user(user))
    
    caption = (
        f"Hᴇʏ 🍿 <b>{user.mention}</b> 🥷\n\n"
        f"📍 <b>Wᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ᴡᴏʀʟᴅ's ᴄᴏᴏʟᴇsᴛ sᴇᴀʀᴄʜ ᴇɴɢɪɴᴇ! ⚡</b>\n\n"
        f"Hᴇʀᴇ ʏᴏᴜ ᴄᴀɴ ʀᴇǫᴜᴇsᴛ ᴍᴏᴠɪᴇs & sᴇʀɪᴇs, ᴊᴜsᴛ sᴇɴᴅ ɴᴀᴍᴇ ᴡɪᴛʜ ᴘʀᴏᴘᴇʀ <b>Gᴏᴏɢʟᴇ sᴘᴇʟʟɪɴɢ</b>..!! 🫧🎬"
    )
    
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔰 Aᴅᴅ Mᴇ Tᴏ Yᴏᴜʀ Gʀᴏᴜᴘ 🔰", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")
        ],
        [
            InlineKeyboardButton("📢 Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ 📢", url=UPDATES_CHANNEL_URL)
        ],
        [
            InlineKeyboardButton("📑 Hᴇʟᴘ", callback_data="help_menu"),
            InlineKeyboardButton("ℹ️ Aʙᴏᴜᴛ", callback_data="about_menu")
        ]
    ])
    
    try:
        await message.reply_photo(photo=START_PIC, caption=caption, reply_markup=buttons)
    except Exception:
        await message.reply_text(text=caption, reply_markup=buttons)

# ==========================================
# 5. MOVIE SEARCH ENGINE (52K MONGODB DATABASE)
# ==========================================
@app.on_message(filters.text & filters.private & ~filters.command(["start", "help", "about"]))
async def search_movie(client, message):
    asyncio.create_task(send_reaction(message))

    raw_query = message.text.strip()
    user = message.from_user
    
    clean_query = re.sub(r"[:_.\-+!?()\[\]]", " ", raw_query)
    words = clean_query.split()
    regex_pattern = ".*".join([re.escape(w) for w in words if len(w) > 0])
    
    results = []
    try:
        results = await asyncio.to_thread(db_search_movies, regex_pattern)
    except Exception as e:
        print(f"MongoDB Search Error: {e}")

    if not results:
        google_query_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(raw_query)}"
        
        no_results_text = (
            f"<b>Sᴏʀʀʏ {user.first_name}</b>, <b>ɴᴏ ғɪʟᴇs ᴡᴇʀᴇ ғᴏᴜɴᴅ ғᴏʀ ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ</b> <code>{raw_query}</code> 🙁\n\n"
            f"<b>Cʜᴇᴄᴋ ʏᴏᴜʀ sᴘᴇʟʟɪɴɢ ɪɴ Gᴏᴏɢʟᴇ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ</b> 😃\n\n"
            f"📝 <b>Mᴏᴠɪᴇ ʀᴇǫᴜᴇsᴛ ғᴏʀᴍᴀᴛ</b> 👇\n\n"
            f"⚜️ <b>E x ᴀ ᴍ ᴘ ʟ ᴇ :</b> <code>Jawan</code> ᴏʀ <code>Jawan 2023</code>\n\n"
            f"📝 <b>Sᴇʀɪᴇs ʀᴇǫᴜᴇsᴛ ғᴏʀᴍᴀᴛ</b> 👇\n\n"
            f"⚜️ <b>E x ᴀ ᴍ ᴘ ʟ ᴇ :</b> <code>Loki S01</code> ᴏʀ <code>Loki S01E04</code> ᴏʀ <code>Lucifer S03E24</code>\n\n"
            f"🚯 <b>Dᴏɴ'ᴛ ᴜsᴇ ➡️</b> <code>':( ! , . /)</code>\n\n"
            f"📌 <i>Iғ ʏᴏᴜʀ sᴘᴇʟʟɪɴɢ ᴀɴᴅ ғᴏʀᴍᴀᴛ ɪs ᴄᴏʀʀᴇᴄᴛ ᴛʜᴇɴ ᴘʟᴇᴀsᴇ ʀᴇᴘᴏʀᴛ ᴛᴏ ᴏᴜʀ sᴜᴘᴘᴏʀᴛ ᴛᴇᴀᴍ 👇</i>"
        )
        
        action_buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔍 Cʜᴇᴄᴋ Sᴘᴇʟʟɪɴɢ Oɴ Gᴏᴏɢʟᴇ 🔍", url=google_query_url)
            ],
            [
                InlineKeyboardButton("🚀 Rᴇᴘᴏʀᴛ Tᴏ Sᴜᴘᴘᴏʀᴛ Tᴇᴀᴍ 🚀", url=SUPPORT_BOT_URL)
            ]
        ])
        
        await message.reply_text(
            text=no_results_text,
            reply_markup=action_buttons,
            disable_web_page_preview=True
        )
        return

    buttons = []
    for res in results:
        file_name = res.get("file_name", "Download Video")
        display_name = (file_name[:40] + "..") if len(file_name) > 42 else file_name
        buttons.append([InlineKeyboardButton(f"📁 {display_name}", callback_data=f"file_{res.get('file_id')}")])

    await message.reply_text(
        f"🎯 <b>Rᴇsᴜʟᴛs ғᴏʀ:</b> <code>{raw_query}</code>\n⚡ <b>Fᴏᴜɴᴅ Fɪʟᴇs:</b> <code>{len(results)}</code>",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ==========================================
# 6. CALLBACK HANDLERS
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
            [
                InlineKeyboardButton("🔰 Aᴅᴅ Mᴇ Tᴏ Yᴏᴜʀ Gʀᴏᴜᴘ 🔰", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")
            ],
            [
                InlineKeyboardButton("📢 Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ 📢", url=UPDATES_CHANNEL_URL)
            ],
            [
                InlineKeyboardButton("📑 Hᴇʟᴘ", callback_data="help_menu"),
                InlineKeyboardButton("ℹ️ Aʙᴏᴜᴛ", callback_data="about_menu")
            ]
        ])
        try:
            await query.message.edit_caption(caption=caption, reply_markup=buttons)
        except Exception:
            await query.message.edit_text(text=caption, reply_markup=buttons)

    elif data == "help_menu":
        help_text = (
            "✨ <b>𝗛𝗢𝗪 𝗧𝗢 𝗚𝗘𝗧 𝗠𝗢𝗩𝗜𝗘𝗦, 𝗔𝗡𝗜𝗠𝗘, 𝗪𝗘𝗕 𝗦𝗘𝗥𝗜𝗘𝗦, 𝗘𝗧𝗖</b> ✨\n\n"
            "1) Sᴇᴀʀᴄʜ ᴛʜᴇ ᴄᴏʀʀᴇᴄᴛ ɴᴀᴍᴇ ᴏɴ ɢᴏᴏɢʟᴇ ᴀɴᴅ ᴄᴏᴘʏ ɪᴛ\n"
            "2) Pᴀsᴛᴇ ᴛʜᴇ ɴᴀᴍᴇ ɪɴ ᴛʜᴇ ʙᴏᴛ ᴀɴᴅ sᴇɴᴅ ɪᴛ\n"
            "(Usᴇ ᴛʜɪs ғᴏʀᴍᴀᴛ ғᴏʀ ʙᴇᴛᴛᴇʀ ʀᴇsᴜʟᴛs)\n\n"
            "📌 <b>Fᴏʀ ᴡᴇʙ-sᴇʀɪᴇs:</b>\n"
            "► Wᴇʙ-sᴇʀɪᴇs ɴᴀᴍᴇ + s01 (Fᴏʀ sᴇᴀsᴏɴ 1, ᴄʜᴀɴɢᴇ ғᴏʀ ᴏᴛʜᴇʀs)\n\n"
            "📌 <b>Fᴏʀ ᴅʀᴀᴍᴀs:</b>\n"
            "► Dʀᴀᴍᴀ ɴᴀᴍᴇ\n\n"
            "📌 <b>Fᴏʀ ᴍᴏᴠɪᴇs:</b>\n"
            "► ᴍᴏᴠɪᴇ ɴᴀᴍᴇ + ʏᴇᴀʀ (Ex: Dʜᴜʀᴀɴᴅʜᴀʀ 2019)\n\n"
            "📌 <b>Fᴏʀ ᴀɴɪᴍᴇ:</b>\n"
            "► ᴀɴɪᴍᴇ ɴᴀᴍᴇ\n\n"
            "🚀 <i>ɪғ ᴀɴʏ ғɪʟᴇs ɴᴏᴛ ᴀᴠᴀɪʟᴀʙʟᴇ ʏᴏᴜ ᴄᴀɴ ʀᴇǫᴜᴇsᴛ ᴜs ʜᴇʀᴇ 👇🏻</i>"
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
            "├⍟ <b>Lɪʙʀᴀʀʏ :</b> <a href='https://github.com/pyrofork/pyrofork'>Pʏʀᴏɢʀᴀᴍ</a>\n"
            "├⍟ <b>Lᴀɴɢᴜᴀɢᴇ :</b> <a href='https://www.python.org'>Pʏᴛʜᴏɴ 3</a>\n"
            "├⍟ <b>Dᴀᴛᴀʙᴀsᴇ :</b> <a href='https://www.mongodb.com'>Mᴏɴɢᴏ DB</a>\n"
            "├⍟ <b>Bᴏᴛ Sᴇʀᴠᴇʀ :</b> <a href='https://render.com'>Rᴇɴᴅᴇʀ</a>\n"
            "├⍟ <b>Bᴜɪʟᴅ Sᴛᴀᴛᴜs :</b> v1.4 [ Sᴛᴀʙʟᴇ 🚀 ]\n"
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
            "ᴀʟʟ ᴛʜᴇ ꜰɪʟᴇꜱ ɪɴ ᴛʜɪꜱ ʙᴏᴛ ᴀʀᴇ ꜰʀᴇᴇʟʏ ᴀᴠᴀɪʟᴀʙʟᴇ ᴏɴ ᴛʜᴇ ɪɴᴛᴇʀɴᴇᴛ ᴏʀ ᴘᴏꜱᴛᴇᴅ ʙʏ ꜱᴏᴍᴇʙᴏᴅʏ ᴇʟꜱᴇ. "
            "ᴊᴜꜱᴛ ꜰᴏʀ ᴇᴀꜱʏ ꜱᴇᴀʀᴄʜɪɴɢ ᴛʜɪꜱ ʙᴏᴛ ɪꜱ ɪɴᴅᴇxɪɴɢ ꜰɪʟᴇꜱ ᴡʜɪᴄʜ ᴀʀᴇ ᴀʟʀᴇᴀᴅʏ ᴜᴘʟᴏᴀᴅᴇᴅ ᴏɴ ᴛᴇʟᴇɢʀᴀᴍ. "
            "ᴡᴇ ʀᴇꜱᴘᴇᴄᴛ ᴀʟʟ ᴛʜᴇ ᴄᴏᴘʏʀɪɢʜᴛ ʟᴀᴡꜱ ᴀɴᴅ ᴡᴏʀᴋꜱ ɪɴ ᴄᴏᴍᴘʟɪᴀɴᴄᴇ ᴡɪᴛʜ ᴅᴍᴄᴀ ᴀɴᴅ ᴇᴜᴄᴅ. "
            "ɪꜰ ᴀɴʏᴛʜɪɴɢ ɪꜱ ᴀɢᴀɪɴꜱᴛ ʟᴀᴡ ᴘʟᴇᴀꜱᴇ ᴄᴏɴᴛᴀᴄᴛ ᴍᴇ ꜱᴏ ᴛʜᴀᴛ ɪᴛ ᴄᴀɴ ʙᴇ ʀᴇᴍᴏᴠᴇᴅ ᴀꜱᴀᴘ. "
            "ɪᴛ ɪꜱ ꜰᴏʙɪʙʙᴇɴ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ, ꜱᴛʀᴇᴀᴍ, ʀᴇᴘʀᴏᴅᴜᴄᴇ, ꜱʜᴀʀᴇ ᴏʀ ᴄᴏɴꜱᴜᴍᴇ ᴄᴏɴᴛᴇɴᴛ ᴡɪᴛʜᴏᴜᴛ ᴇxᴘʟɪᴄɪᴛ "
            "ᴘᴇʀᴍɪꜱꜱɪᴏɴ ꜰʀᴏᴍ ᴛʜᴇ ᴄᴏɴᴛᴇɴᴛ ᴄʀᴇᴀᴛᴏʀ or ʟᴇɢᴀʟ ᴄᴏᴘʏʀɪɢʜᴛ ʜᴏʟᴅᴇʀ. "
            "ɪꜰ ʏᴏᴜ ʙᴇʟɪᴇᴠᴇ ᴛʜɪꜱ ʙᴏᴛ ɪꜱ ᴠɪᴏʟᴀᴛɪɴɢ ʏᴏᴜʀ ɪɴᴛᴇʟʟᴇᴄᴛᴜᴀʟ ᴘʀᴏᴘᴇʀᴛʏ, ᴄᴏɴᴛᴀᴄᴛ ᴛʜᴇ ʀᴇꜱᴘᴇᴄᴛɪᴠᴇ ᴄʜᴀɴɴᴇʟꜱ ꜰᴏʀ ʀᴇᴍᴏᴠᴀʟ. "
            "ᴛʜᴇ ʙᴏᴛ ᴅᴏᴇꜱ ɴᴏᴛ ᴏᴡɴ ᴀɴʏ ᴏꜰ ᴛHᴇꜱᴇ ᴄᴏɴᴛᴇɴᴛꜱ, ɪᴛ ᴏɴʟʏ ɪɴᴅᴇx ᴛʜᴇ ꜰɪʟᴇꜱ ꜰʀᴏᴍ ᴛᴇʟᴇɢʀᴀᴍ."
        )
        disclaimer_buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("⇋ Bᴀᴄᴋ ⇋", callback_data="about_menu")]
        ])
        try:
            await query.message.edit_caption(caption=disclaimer_text, reply_markup=disclaimer_buttons)
        except Exception:
            await query.message.edit_text(text=disclaimer_text, reply_markup=disclaimer_buttons)

    elif data.startswith("file_"):
        file_id = data.split("file_", 1)[1]
        try:
            await client.send_cached_media(chat_id=query.from_user.id, file_id=file_id)
        except Exception:
            await query.answer("❌ File pathate somosya hoyeche!", show_alert=True)

# ==========================================
# 7. REAL-TIME AUTO INDEXER (NEW UPLOADS)
# ==========================================
@app.on_message(filters.channel & (filters.document | filters.video | filters.audio))
async def channel_indexer(client, message):
    if message.chat.id == DB_CHANNEL:
        media = message.document or message.video or message.audio
        if media and getattr(media, "file_size", 0) >= (100 * 1024 * 1024):
            cap = message.caption.html if message.caption else ""
            await asyncio.to_thread(db_save_new_file, media, message.id, cap)

# ==========================================
# 8. MAIN RUNNER (BOT + LOG + WEB SERVER)
# ==========================================
async def main():
    await app.start()
    print("🚀 BoultFlix Bot Started Successfully!")

    if LOG_CHANNEL:
        try:
            startup_text = (
                f"⚡ <b>Bᴏᴜʟᴛғʟɪx Mᴏᴠɪᴇs Bᴏᴛ Rᴇsᴛᴀʀᴛᴇᴅ!</b> 🚀\n\n"
                f"👤 <b>Dᴇᴠᴇʟᴏᴘᴇʀ:</b> @BoultFlix\n"
                f"🌐 <b>Sᴇʀᴠᴇʀ:</b> Rᴇɴᴅᴇʀ\n"
                f"🟢 <b>Sᴛᴀᴛᴜs:</b> Oɴʟɪɴᴇ & Rᴇᴀᴅʏ"
            )
            await app.send_message(LOG_CHANNEL, startup_text)
            print("📢 Startup notification sent to Log Channel!")
        except Exception as e:
            print(f"⚠️ Log Channel Alert Error: {e}")

    await start_web_server()
    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
