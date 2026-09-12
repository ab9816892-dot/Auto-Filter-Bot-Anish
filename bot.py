import os
import re
import time
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
# 1. CONFIGURATION
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

REACTION_EMOJIS = [
    "🔥", "⚡", "❤️", "🍿", "🥰", "🎉", "🤩", "👏", 
    "👌", "🕊️", "😍", "💯", "💖", "🍓", "🍾", "😎", 
    "👾", "✨", "🤙", "🥂", "🎬", "🏆", "💎", "👻", 
    "🚀", "👑", "🫡", "🤝", "💫", "🌟"
]

# MongoDB Connection (Dual Collection Fallback for 52k Movies)
MONGO_URI = "mongodb+srv://ab9816892_db_user:anish12345@cluster0.yogzcqw.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

db_cluster = mongo_client["Cluster0"]
files_col = db_cluster["Telegram_Files"]
files_col_alt = db_cluster["telegram_files"]
users_col = db_cluster["Users"]

app = Client(
    "BoultFlix_Rpeditz_Engine",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ==========================================
# 2. RENDER PORT KEEP-ALIVE SERVER
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
        return "N/A"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} GB"

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
        query = {"file_name": {"$regex": query_pattern, "$options": "i"}}
        results = list(files_col.find(query).limit(10))
        total = files_col.count_documents(query)
        if not results:
            results = list(files_col_alt.find(query).limit(10))
            total = files_col_alt.count_documents(query)
        return results, total
    except Exception as e:
        print(f"DB Search Error: {e}", flush=True)
        return [], 0

def db_get_file_by_id(doc_id):
    try:
        doc = files_col.find_one({"_id": ObjectId(doc_id)})
        if not doc:
            doc = files_col_alt.find_one({"_id": ObjectId(doc_id)})
        return doc
    except Exception:
        return None

# ==========================================
# 4. /START HANDLER (IMAGE 3 & DIRECT FILE LINK)
# ==========================================
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    asyncio.create_task(send_reaction(message))
    user = message.from_user

    # Handle Deep Links (e.g. /start file_64b...)
    if len(message.command) > 1 and message.command[1].startswith("file_"):
        doc_id = message.command[1].replace("file_", "")
        doc = await asyncio.to_thread(db_get_file_by_id, doc_id)
        if doc and doc.get("file_id"):
            file_btn = InlineKeyboardMarkup([
                [InlineKeyboardButton("📌 JOIN UPDATES CHANNEL 📌", url=UPDATES_CHANNEL_URL)]
            ])
            try:
                caption = f"📁 <b>FILENAME :</b> {doc.get('file_name', 'Movie File')}\n\n⚙️ <b>SIZE :</b> {format_size(doc.get('file_size', 0))}"
                sent_file = await client.send_cached_media(
                    chat_id=user.id,
                    file_id=doc["file_id"],
                    caption=caption,
                    reply_markup=file_btn
                )
                
                # Auto delete warning timer
                warn_text = "⚠️ <b>THIS MOVIE FILE/VIDEO WILL BE DELETED IN 5 MINUTE\n\n<i>PLEASE FORWARD THIS FILE TO SOMEWHERE ELSE & START DOWNLOADING THERE</i></b>"
                warn_msg = await message.reply_text(warn_text)

                async def delete_after_5_mins():
                    await asyncio.sleep(300)
                    try:
                        await sent_file.delete()
                        await warn_msg.edit_text("❌ <b>YOUR VIDEO / FILE IS SUCCESSFULLY DELETED TO PROTECT THIS BOT FROM COPYRIGHT TAKEDOWN ✨🎬</b>")
                    except Exception:
                        pass

                asyncio.create_task(delete_after_5_mins())
                return
            except Exception as e:
                print(f"Direct send error: {e}", flush=True)

    # Standard /start Greeting
    asyncio.create_task(asyncio.to_thread(db_add_user, user.id, user.first_name))
    caption = (
        f"Hᴇʏ 🍿 <b>{user.mention}</b> 🥷\n\n"
        f"📍 <b>Wᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ᴡᴏʀʟᴅ's ᴄᴏᴏʟᴇsᴛ sᴇᴀʀᴄʜ ᴇɴɢɪɴᴇ! ⚡</b>\n\n"
        f"Hᴇʀᴇ ʏᴏᴜ ᴄᴀɴ ʀᴇǫᴜᴇsᴛ ᴍᴏᴠɪᴇs & sᴇʀɪᴇs, ᴊᴜsᴛ sᴇɴᴅ ɴᴀᴍᴇ ᴡɪᴛʜ ᴘʀᴏᴘᴇʀ <b>Gᴏᴏɢʟᴇ sᴘᴇʟʟɪɴɢ</b>..!! 🫧🎬"
    )
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔰 Aᴅᴅ Mᴇ Tᴏ Yᴏᴜʀ Gʀᴏᴜᴘ 🔰", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
        [InlineKeyboardButton("📢 Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ 📢", url=UPDATES_CHANNEL_URL)],
        [InlineKeyboardButton("📑 Hᴇʟᴘ", callback_data="help_menu"), InlineKeyboardButton("ℹ️ Aʙᴏᴜᴛ", callback_data="about_menu")]
    ])
    
    try:
        await message.reply_photo(photo=START_PIC, caption=caption, reply_markup=buttons)
    except Exception:
        await message.reply_text(text=caption, reply_markup=buttons)

# ==========================================
# 5. RPEDITZ STYLE MOVIE SEARCH ENGINE (IMAGE 6 & IMAGE 2)
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

    results, total = await asyncio.to_thread(db_search_movies, regex_pattern)
    time_taken = f"{time.time() - start_time:.2f}"

    # No Results Found Screen (Image 2 Exact Text)
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
            [InlineKeyboardButton("🔍 Cʜᴇᴄᴋ Sᴘᴇʟʟɪɴɢ Oɴ Gᴏᴏɢʟᴇ 🔍", url=google_query_url)],
            [InlineKeyboardButton("🚀 Rᴇᴘᴏʀᴛ Tᴏ Sᴜᴘᴘᴏʀᴛ Tᴇᴀᴍ 🚀", url=SUPPORT_BOT_URL)]
        ])
        await message.reply_text(text=no_results_text, reply_markup=action_buttons, disable_web_page_preview=True)
        return

    # RPEDITZ Full Results Template (Image 6 Exact Match)
    res_text = (
        f"<b>TITLE :</b> <code>{raw_query}</code>\n"
        f"📁 <b>TOTAL FILES :</b> <code>{total}</code>\n"
        f"⏳ <b>RESULT IN :</b> <code>{time_taken} SECONDS</code>\n\n"
        f"🧃 <b>REQUESTED BY :</b> {user.mention}\n"
        f"⚜️ <b>POWERED BY :</b> HD PRO SEARCH BOT ⚡\n\n"
        f"<b><u>Your Requested Files Are Here</u></b>\n\n"
    )

    doc_ids_all = []
    for idx, doc in enumerate(results, start=1):
        doc_id = str(doc.get("_id"))
        doc_ids_all.append(doc_id)
        f_name = doc.get("file_name", "Movie File")
        f_size = format_size(doc.get("file_size", 0))
        link = f"https://t.me/{BOT_USERNAME}?start=file_{doc_id}"
        res_text += f"{idx}. <a href='{link}'>[{f_size}] {f_name}</a>\n\n"

    rpeditz_buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("REMOVE ADS", callback_data="btn_filter"), InlineKeyboardButton("⚡ SEND ALL", callback_data="btn_sendall")],
        [
            InlineKeyboardButton("QUALITY", callback_data="btn_quality"),
            InlineKeyboardButton("LANGUAGE", callback_data="btn_language"),
            InlineKeyboardButton("SEASON", callback_data="btn_season")
        ],
        [
            InlineKeyboardButton("PAGE", callback_data="btn_page"),
            InlineKeyboardButton("1/1", callback_data="btn_page"),
            InlineKeyboardButton("NEXT ➢", callback_data="btn_page")
        ],
        [InlineKeyboardButton("« NO MORE PAGES AVAILABLE »", callback_data="btn_page")]
    ])

    await message.reply_text(
        text=res_text,
        reply_markup=rpeditz_buttons,
        disable_web_page_preview=True
    )

# ==========================================
# 6. CALLBACK HANDLERS (IMAGE 3, 4, 5 & FILTERS)
# ==========================================
@app.on_callback_query()
async def bot_callbacks(client, query: CallbackQuery):
    data = query.data

    if data == "home_menu":
        await query.answer("Share & Support Us ❤️")
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
        await query.answer("Help Menu")
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
        await query.answer("About Details")
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
        await query.answer("Disclaimer")
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

    elif data == "btn_quality":
        await query.answer("Select Quality")
        q_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("360P", callback_data="btn_page"), InlineKeyboardButton("480P", callback_data="btn_page")],
            [InlineKeyboardButton("720P", callback_data="btn_page"), InlineKeyboardButton("1080P", callback_data="btn_page")],
            [InlineKeyboardButton("1440P", callback_data="btn_page"), InlineKeyboardButton("2160P", callback_data="btn_page")],
            [InlineKeyboardButton("4K", callback_data="btn_page")],
            [InlineKeyboardButton("« BACK TO FILES »", callback_data="home_menu")]
        ])
        try:
            await query.message.edit_text("⚙️ <b>Sᴇʟᴇᴄᴛ Qᴜᴀʟɪᴛʏ 👇</b>", reply_markup=q_markup)
        except Exception:
            pass

    elif data == "btn_language":
        await query.answer("Select Language")
        l_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("MALAYALAM", callback_data="btn_page"), InlineKeyboardButton("TAMIL", callback_data="btn_page")],
            [InlineKeyboardButton("ENGLISH", callback_data="btn_page"), InlineKeyboardButton("HINDI", callback_data="btn_page")],
            [InlineKeyboardButton("TELUGU", callback_data="btn_page"), InlineKeyboardButton("KANNADA", callback_data="btn_page")],
            [InlineKeyboardButton("GUJARATI", callback_data="btn_page"), InlineKeyboardButton("MARATHI", callback_data="btn_page")],
            [InlineKeyboardButton("PUNJABI", callback_data="btn_page"), InlineKeyboardButton("DUAL AUDIO", callback_data="btn_page")],
            [InlineKeyboardButton("« BACK TO FILES »", callback_data="home_menu")]
        ])
        try:
            await query.message.edit_text("🌐 <b>Sᴇʟᴇᴄᴛ Lᴀɴɢᴜᴀɢᴇ 👇</b>", reply_markup=l_markup)
        except Exception:
            pass

    elif data == "btn_season":
        await query.answer("Select Season")
        s_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("SEASON 1", callback_data="btn_page"), InlineKeyboardButton("SEASON 2", callback_data="btn_page")],
            [InlineKeyboardButton("SEASON 3", callback_data="btn_page"), InlineKeyboardButton("SEASON 4", callback_data="btn_page")],
            [InlineKeyboardButton("SEASON 5", callback_data="btn_page"), InlineKeyboardButton("SEASON 6", callback_data="btn_page")],
            [InlineKeyboardButton("« BACK TO FILES »", callback_data="home_menu")]
        ])
        try:
            await query.message.edit_text("🎬 <b>Sᴇʟᴇᴄᴛ Sᴇᴀsᴏɴ 👇</b>", reply_markup=s_markup)
        except Exception:
            pass

    elif data in ["btn_filter", "btn_sendall", "btn_page"]:
        await query.answer("⚡ Direct links theke file open koro!", show_alert=False)

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
