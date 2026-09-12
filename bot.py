import os
import re
import math
import uuid
import logging
import asyncio
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from pyrogram.errors import UserNotParticipant
from config import (
    API_ID, API_HASH, BOT_TOKEN, BOT_USERNAME, ADMINS, CHANNELS, 
    FORCE_SUB_CHANNEL, UPDATE_CHANNEL, TMDB_API_KEY, AUTO_POST,
    USE_SHORTLINK, SHORTLINK_URL, SHORTLINK_API
)
from database import db_instance
from template import Script

logging.basicConfig(level=logging.INFO)

app = Client(
    "AutoFilterBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# 1. Clean Junk / Ads / Site Names from Filenames
def clean_file_title(filename):
    clean = re.sub(r"(@\w+|\[@\w+\]|\[.*?\]|\(.*?\)|www\.\S+|https?://\S+|HDHub4u\w*|TamilBlasters\w*)", "", filename, flags=re.IGNORECASE)
    clean = re.sub(r"(1080p|720p|480p|2160p|4k|HEVC|x264|x265|HDRip|HDTV|WEB-DL|WEB_DL|BluRay|AAC|ESub|ESubs|Dual|Multi)", "", clean, flags=re.IGNORECASE)
    clean = clean.replace(".", " ").replace("_", " ").replace("-", " ")
    return " ".join(clean.split())

# 2. TMDb Metadata & ID Fetcher
async def fetch_tmdb_metadata(query):
    clean_name = clean_file_title(query)
    search_term = " ".join(clean_name.split()[:3])
    url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_API_KEY}&query={search_term}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                if data.get("results"):
                    res = data["results"][0]
                    title = res.get("title") or res.get("name") or search_term
                    poster_path = res.get("poster_path")
                    poster = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else "https://envs.sh/default_poster.jpg"
                    rating = str(res.get("vote_average", "8.5"))[:3]
                    media_type = res.get("media_type", "tv").lower()
                    tmdb_id = res.get("id", "262838")
                    
                    tmdb_url = f"https://www.themoviedb.org/{media_type}/{tmdb_id}"
                    type_tag = "SERIES" if media_type == "tv" else "MOVIE"
                    
                    return {
                        "title": title, 
                        "poster": poster, 
                        "rating": rating, 
                        "type": type_tag,
                        "tmdb_url": tmdb_url
                    }
    except Exception:
        pass
        
    return {
        "title": search_term.title(),
        "poster": "https://envs.sh/default_poster.jpg",
        "rating": "8.5",
        "type": "SERIES",
        "tmdb_url": "https://www.themoviedb.org"
    }

async def get_shortlink(long_url):
    api_url = f"https://{SHORTLINK_URL}/api?api={SHORTLINK_API}&url={long_url}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as resp:
                data = await resp.json()
                return data.get("shortenedUrl", long_url)
    except Exception:
        return long_url

async def is_subscribed(client, user_id):
    if not FORCE_SUB_CHANNEL:
        return True
    try:
        user = await client.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        if user.status in ["banned", "left"]:
            return False
        return True
    except UserNotParticipant:
        return False
    except Exception:
        return True

def format_size(size):
    if not size:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

# 3. Exact 1st Image Search Layout Generator
def create_advanced_search_layout(results, query, page=1):
    PER_PAGE = 10
    total_results = len(results)
    total_pages = math.ceil(total_results / PER_PAGE) or 1
    
    start_idx = (page - 1) * PER_PAGE
    end_idx = start_idx + PER_PAGE
    page_files = results[start_idx:end_idx]
    
    # Message Body: Numbered Hyperlinks (Image 1 Style)
    msg_text = "⚡ **POWERED BY : ⚡ HD PRO SEARCH BOT 🕶**\n\n"
    msg_text += "<b>Your Requested Files Are Here</b>\n\n"
    
    file_ids = []
    for i, file in enumerate(page_files, start=start_idx + 1):
        size_str = format_size(file.get('file_size', 0))
        clean_name = file['file_name'].replace("_", " ")
        file_url = f"https://t.me/{BOT_USERNAME}?start=getfile_{file['file_id']}"
        msg_text += f"**{i}.** [{size_str}] [{clean_name}]({file_url})\n\n"
        file_ids.append(file['file_id'])
    
    # Buttons (Image 1 Layout)
    buttons = [
        [
            InlineKeyboardButton("REMOVE ADS ↗", callback_data="verify_token"),
            InlineKeyboardButton("SEND ALL", callback_data=f"sendall#{query}#{page}")
        ],
        [
            InlineKeyboardButton("QUALITY", callback_data=f"filter_qual#{query}"),
            InlineKeyboardButton("LANGUAGE", callback_data=f"filter_lang#{query}"),
            InlineKeyboardButton("SEASON", callback_data=f"filter_season#{query}")
        ]
    ]
    
    # Pagination Navigation
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("⏮ PREV", callback_data=f"page#{query}#{page-1}"))
    else:
        nav.append(InlineKeyboardButton("PAGE", callback_data="ignore"))
        
    nav.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="pages_count"))
    
    if page < total_pages:
        nav.append(InlineKeyboardButton("NEXT ⏩", callback_data=f"page#{query}#{page+1}"))
        
    buttons.append(nav)
    return msg_text, InlineKeyboardMarkup(buttons)

# 4. /start Command Handler
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message: Message):
    await db_instance.add_user(message.from_user.id)
    
    if len(message.command) > 1:
        param = message.command[1]
        
        if param.startswith("verify_"):
            await db_instance.set_user_verified(message.from_user.id)
            await message.reply_text("🎉 **24-Hours Verification Successful!**\nAb aap 24 ghante tak direct sabhi files download kar sakte hain.")
            return

        if param.startswith("getfile_"):
            file_id = param.split("_", 1)[1]
            if USE_SHORTLINK and not await db_instance.is_user_verified(message.from_user.id):
                token = str(uuid.uuid4())[:8]
                verify_url = await get_shortlink(f"https://t.me/{BOT_USERNAME}?start=verify_{token}")
                btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔓 Verify 24hr Access Token", url=verify_url)]])
                await message.reply_text("⚠️ File download karne ke liye 24hr token verify karein:", reply_markup=btn)
                return

            caption = Script.CUSTOM_FILE_CAPTION.format(file_name="Requested File", file_size="HD", bot_username=BOT_USERNAME)
            await client.send_cached_media(chat_id=message.from_user.id, file_id=file_id, caption=caption)
            return

    if not await is_subscribed(client, message.from_user.id):
        buttons = [
            [InlineKeyboardButton("📢 Join Update Channel", url=f"https://t.me/{str(FORCE_SUB_CHANNEL).replace('@', '')}")],
            [InlineKeyboardButton("🔄 Try Again", callback_data="check_sub")]
        ]
        await message.reply_text(Script.FORCE_SUB_TEXT, reply_markup=InlineKeyboardMarkup(buttons))
        return

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Updates Channel", url=f"https://t.me/{str(FORCE_SUB_CHANNEL).replace('@', '')}"), 
         InlineKeyboardButton("💬 Support Group", url="https://t.me/")]
    ])
    await message.reply_text(
        text=Script.START_TEXT.format(message.from_user.first_name),
        reply_markup=buttons,
        disable_web_page_preview=True
    )

# 5. Target Channel Auto-Index & TMDb Poster Auto-Post
@app.on_message(filters.chat(CHANNELS) & (filters.document | filters.video | filters.audio))
async def media_indexer(client, message: Message):
    media = message.document or message.video or message.audio
    if media:
        raw_name = getattr(media, "file_name", None) or message.caption or "Unknown Movie"
        file_data = {
            "file_id": media.file_id,
            "file_name": raw_name,
            "file_size": media.file_size,
            "mime_type": getattr(media, "mime_type", "")
        }
        await db_instance.save_file(file_data)

        if AUTO_POST and UPDATE_CHANNEL:
            meta = await fetch_tmdb_metadata(raw_name)
            caption = Script.POST_TEMPLATE.format(
                media_type=meta["type"],
                tmdb_url=meta["tmdb_url"],
                title=meta["title"],
                genres="Animation, Mystery",
                ott="Crunchyroll",
                rating=meta["rating"],
                episodes="S1 : 1",
                bot_name="HD Pro Search Bot",
                bot_username=BOT_USERNAME
            )
            
            btn = InlineKeyboardMarkup([[
                InlineKeyboardButton("ɢᴇᴛ ғɪʟᴇs ↗", url=f"https://t.me/{BOT_USERNAME}?start=getfile_{media.file_id}")
            ]])
            
            try:
                await client.send_photo(
                    chat_id=UPDATE_CHANNEL,
                    photo=meta["poster"],
                    caption=caption,
                    reply_markup=btn
                )
            except Exception as e:
                logging.error(f"Auto-post failed: {e}")

# 6. PM Search Engine
@app.on_message(filters.text & ~filters.command(["start", "help", "about", "stats"]))
async def auto_filter(client, message: Message):
    if message.chat.type.name == "PRIVATE":
        if not await is_subscribed(client, message.from_user.id):
            buttons = [
                [InlineKeyboardButton("📢 Join Update Channel", url=f"https://t.me/{str(FORCE_SUB_CHANNEL).replace('@', '')}")],
                [InlineKeyboardButton("🔄 Try Again", callback_data="check_sub")]
            ]
            await message.reply_text(Script.FORCE_SUB_TEXT, reply_markup=InlineKeyboardMarkup(buttons))
            return

    query = message.text.strip()
    if len(query) < 2:
        return
    
    results = await db_instance.search_media(query)
    if not results:
        await message.reply_text(
            f"❌ <b>'{query}'</b> nahi mila!\n\n💡 Spelling sahi karein aur dobara try karein.",
            quote=True
        )
        return
    
    msg_text, reply_markup = create_advanced_search_layout(results, query, page=1)
    await message.reply_text(
        text=msg_text,
        reply_markup=reply_markup,
        disable_web_page_preview=True,
        quote=True
    )

# 7. Pagination Callback
@app.on_callback_query(filters.regex(r"^page#"))
async def pagination_handler(client, query: CallbackQuery):
    data_parts = query.data.split("#")
    search_query = data_parts[1]
    page_num = int(data_parts[2])
    
    results = await db_instance.search_media(search_query)
    if not results:
        await query.answer("❌ Koi file nahi mili!", show_alert=True)
        return
        
    msg_text, reply_markup = create_advanced_search_layout(results, search_query, page=page_num)
    try:
        await query.message.edit_text(text=msg_text, reply_markup=reply_markup, disable_web_page_preview=True)
    except Exception:
        pass
    await query.answer()

# 8. Filter Menu Callbacks (Quality / Language / Season)
@app.on_callback_query(filters.regex(r"^filter_qual#"))
async def filter_quality_menu(client, query: CallbackQuery):
    q = query.data.split("#")[1]
    buttons = [
        [
            InlineKeyboardButton("480p", callback_data=f"filterapply#{q} 480p"),
            InlineKeyboardButton("720p", callback_data=f"filterapply#{q} 720p"),
            InlineKeyboardButton("1080p", callback_data=f"filterapply#{q} 1080p")
        ],
        [
            InlineKeyboardButton("2160p (4K)", callback_data=f"filterapply#{q} 4k"),
            InlineKeyboardButton("HEVC", callback_data=f"filterapply#{q} HEVC")
        ],
        [InlineKeyboardButton("🔙 Back to Results", callback_data=f"page#{q}#1")]
    ]
    await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))

@app.on_callback_query(filters.regex(r"^filter_lang#"))
async def filter_lang_menu(client, query: CallbackQuery):
    q = query.data.split("#")[1]
    buttons = [
        [
            InlineKeyboardButton("Hindi", callback_data=f"filterapply#{q} Hindi"),
            InlineKeyboardButton("English", callback_data=f"filterapply#{q} English"),
            InlineKeyboardButton("Telugu", callback_data=f"filterapply#{q} Telugu")
        ],
        [
            InlineKeyboardButton("Tamil", callback_data=f"filterapply#{q} Tamil"),
            InlineKeyboardButton("Punjabi", callback_data=f"filterapply#{q} Punjabi"),
            InlineKeyboardButton("Bengali", callback_data=f"filterapply#{q} Bengali")
        ],
        [InlineKeyboardButton("🔙 Back to Results", callback_data=f"page#{q}#1")]
    ]
    await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))

@app.on_callback_query(filters.regex(r"^filter_season#"))
async def filter_season_menu(client, query: CallbackQuery):
    q = query.data.split("#")[1]
    buttons = [
        [
            InlineKeyboardButton("Season 1", callback_data=f"filterapply#{q} S01"),
            InlineKeyboardButton("Season 2", callback_data=f"filterapply#{q} S02")
        ],
        [
            InlineKeyboardButton("Season 3", callback_data=f"filterapply#{q} S03"),
            InlineKeyboardButton("Season 4", callback_data=f"filterapply#{q} S04")
        ],
        [InlineKeyboardButton("🔙 Back to Results", callback_data=f"page#{q}#1")]
    ]
    await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))

@app.on_callback_query(filters.regex(r"^filterapply#"))
async def filter_apply_handler(client, query: CallbackQuery):
    new_query = query.data.split("#")[1]
    results = await db_instance.search_media(new_query)
    if not results:
        await query.answer("❌ Iss filter ke saath koi file nahi mili!", show_alert=True)
        return
    msg_text, reply_markup = create_advanced_search_layout(results, new_query, page=1)
    await query.message.edit_text(text=msg_text, reply_markup=reply_markup, disable_web_page_preview=True)

# 9. Send All Files from Current Page
@app.on_callback_query(filters.regex(r"^sendall#"))
async def send_all_handler(client, query: CallbackQuery):
    user_id = query.from_user.id
    if USE_SHORTLINK and not await db_instance.is_user_verified(user_id):
        token = str(uuid.uuid4())[:8]
        verify_url = await get_shortlink(f"https://t.me/{BOT_USERNAME}?start=verify_{token}")
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔓 Verify 24hr Access Token", url=verify_url)]])
        await query.message.reply_text("⚠️ Send All use karne ke liye 24hr token verify karein:", reply_markup=btn)
        return
        
    data_parts = query.data.split("#")
    search_query = data_parts[1]
    page_num = int(data_parts[2])
    
    results = await db_instance.search_media(search_query)
    PER_PAGE = 10
    start_idx = (page_num - 1) * PER_PAGE
    end_idx = start_idx + PER_PAGE
    page_files = results[start_idx:end_idx]
    
    await query.answer("📤 Sending all files...")
    for f in page_files:
        caption = Script.CUSTOM_FILE_CAPTION.format(file_name=f['file_name'], file_size="HD", bot_username=BOT_USERNAME)
        try:
            await client.send_cached_media(chat_id=user_id, file_id=f['file_id'], caption=caption)
            await asyncio.sleep(0.5)
        except Exception:
            pass

# 10. Remove Ads / Verification Callback
@app.on_callback_query(filters.regex("verify_token"))
async def verify_token_callback(client, query: CallbackQuery):
    token = str(uuid.uuid4())[:8]
    verify_url = await get_shortlink(f"https://t.me/{BOT_USERNAME}?start=verify_{token}")
    btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔓 Bypass / Verify Access Token", url=verify_url)]])
    await query.message.reply_text(
        "✨ **Remove Ads / 24-Hour Access:**\n\nNiche diye link se token verify karein, 24 ghante sabhi movies direct bina kisi rukawat ke download karein.",
        reply_markup=btn
    )

@app.on_callback_query(filters.regex("check_sub"))
async def check_sub_handler(client, query: CallbackQuery):
    if not await is_subscribed(client, query.from_user.id):
        await query.answer("❌ Pehle channel join karein!", show_alert=True)
        return
    await query.message.delete()
    await query.message.reply_text("✅ Verification Successful! Ab aap search kar sakte hain.")

@app.on_callback_query(filters.regex(r"^(ignore|pages_count)$"))
async def ignore_handler(client, query: CallbackQuery):
    await query.answer()

@app.on_message(filters.command("stats") & filters.user(ADMINS))
async def stats_handler(client, message: Message):
    total_users = await db_instance.total_users_count()
    total_files = await db_instance.total_files_count()
    await message.reply_text(
        f"📊 <b>Bot Database Stats:</b>\n\n"
        f"👥 Total Users: <code>{total_users}</code>\n"
        f"📁 Total Indexed Files: <code>{total_files}</code>"
    )

if __name__ == "__main__":
    app.run()
