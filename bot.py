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

# MongoDB Connection
MONGO_URI = "mongodb+srv://ab9816892_db_user:anish12345@cluster0.yogzcqw.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = mongo_client["Cluster0"]
files_col = db["Telegram_Files"]
users_col = db["Users"]

app = Client(
    "BoultFlix_Rpeditz_Fixed",
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
        return "0 B"
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
# 4. /START HANDLER
# ==========================================
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    asyncio.create_task(send_reaction(message))
    user = message.from_user

    if len(message.command) > 1 and message.command[1].startswith("file_"):
        doc_id = message.command[1].replace("file_", "")
        doc = await asyncio.to_thread(db_get_file_by_id, doc_id)
        if doc and doc.get("file_id"):
            file_btn = InlineKeyboardMarkup([
                [InlineKeyboardButton("📌 JOIN UPDATES CHANNEL 📌", url=UPDATES_CHANNEL_URL)]
            ])
            try:
                caption = f"📁 <b>FILENAME :</b> {doc.get('file_name', 'Movie File')}\n\n⚙️ <b>SIZE :</b> {format_size(doc.get('file_size', 0))}"
                await client.send_cached_media(
                    chat_id=user.id,
                    file_id=doc["file_id"],
                    caption=caption,
                    reply_markup=file_btn
                )
                return
            except Exception as e:
                print(f"File Delivery Error: {e}", flush=True)

    asyncio.create_task(asyncio.to_thread(db_add_user, user.id, user.first_name))
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
# 5. RPEDITZ STYLE MOVIE SEARCH
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

    res_text = (
        f"<b>TITLE :</b> <code>{raw_query}</code>\n"
        f"📁 <b>TOTAL FILES :</b> <code>{total}</code>\n"
        f"⏳ <b>RESULT IN :</b> <code>{time_taken} SECONDS</code>\n\n"
        f"🧃 <b>REQUESTED BY :</b> {user.mention}\n"
        f"⚜️ <b>POWERED BY :</b> <a href='https://t.me/{BOT_USERNAME}'>HD PRO SEARCH BOT</a> ⚡\n\n"
        f"<b><u>Your Requested Files Are Here</u></b>\n\n"
    )

    for idx, doc in enumerate(results, start=1):
        doc_id = str(doc.get("_id"))
        f_name = doc.get("file_name", "Movie File")
        f_size = format_size(doc.get("file_size", 0))
        link = f"https://t.me/{BOT_USERNAME}?start=file_{doc_id}"
        res_text += f"{idx}. <a href='{link}'>[{f_size}] {f_name}</a>\n\n"

    # Safe button callback data to prevent ButtonDataInvalid error
    rpeditz_buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ SEND ALL", callback_data="sendall_files")],
        [
            InlineKeyboardButton("QUALITY", callback_data="btn_filter"),
            InlineKeyboardButton("LANGUAGE", callback_data="btn_filter"),
            InlineKeyboardButton("SEASON", callback_data="btn_filter")
        ],
        [
            InlineKeyboardButton("PAGE", callback_data="btn_page"),
            InlineKeyboardButton("1/1", callback_data="btn_page"),
            InlineKeyboardButton("NEXT ➢", callback_data="btn_page")
        ]
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
            "ᴊᴜꜱᴛ ꜰᴏʀ ᴇᴀꜱʏ ꜱᴇᴀʀᴄʜɪɴɢ ᴛʜɪꜱ ʙᴏᴛ ɪꜱ ɪɴᴅᴇxɪɴɢ ꜰɪʟᴇꜱ ᴡHɪᴄʜ ᴀʀᴇ ᴀʟʀᴇᴀᴅʏ ᴜᴘʟᴏᴀᴅᴇᴅ ᴏɴ ᴛᴇʟᴇɢʀᴀᴍ."
        )
        disclaimer_buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("⇋ Bᴀᴄᴋ ⇋", callback_data="about_menu")]
        ])
        try:
            await query.message.edit_caption(caption=disclaimer_text, reply_markup=disclaimer_buttons)
        except Exception:
            await query.message.edit_text(text=disclaimer_text, reply_markup=disclaimer_buttons)

    elif data == "sendall_files":
        await query.answer("Fetching top results for you... 🍿")
        # Send top 3 files safely
        cursor = files_col.find().limit(3)
        for doc in cursor:
            if doc and doc.get("file_id"):
                file_btn = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📌 JOIN UPDATES CHANNEL 📌", url=UPDATES_CHANNEL_URL)]
                ])
                try:
                    caption = f"📁 <b>FILENAME :</b> {doc.get('file_name', 'Movie File')}\n\n⚙️ <b>SIZE :</b> {format_size(doc.get('file_size', 0))}"
                    await client.send_cached_media(
                        chat_id=query.from_user.id,
                        file_id=doc["file_id"],
                        caption=caption,
                        reply_markup=file_btn
                    )
                    await asyncio.sleep(0.5)
                except Exception:
                    pass

    elif data in ["btn_filter", "btn_page"]:
        await query.answer("Use the direct movie links above! ⚡", show_alert=False)

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
