import os
import re
import math
import uuid
import logging
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

# 1. Clean Junk & Release Tags from Filename
def clean_file_title(filename):
    clean = re.sub(r"(@\w+|\[.*?\]|\(.*?\)|www\.\w+\.\w+|https?://\S+)", "", filename)
    clean = re.sub(r"(1080p|720p|480p|2160p|4k|HEVC|x264|x265|HDRip|HDTV|WEB-DL|BluRay|AAC|ESub|Dual|Multi)", "", clean, flags=re.IGNORECASE)
    clean = clean.replace(".", " ").replace("_", " ").replace("-", " ")
    return " ".join(clean.split())

# 2. Async TMDb Metadata & ID Scraper for Dynamic Hyperlink
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
                    
                    # Direct TMDb Page URL for Header Hyperlink
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

# 3. Shortlink Generator
async def get_shortlink(long_url):
    api_url = f"https://{SHORTLINK_URL}/api?api={SHORTLINK_API}&url={long_url}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as resp:
                data = await resp.json()
                return data.get("shortenedUrl", long_url)
    except Exception:
        return long_url

# 4. Force Subscribe Check
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

# 5. Pagination Buttons
def create_search_markup(results, query, page=1):
    buttons = []
    buttons.append([InlineKeyboardButton(f"🎬 {query.title()} 🎬", callback_data="ignore")])
    
    PER_PAGE = 10
    total_results = len(results)
    total_pages = math.ceil(total_results / PER_PAGE) or 1
    
    start_idx = (page - 1) * PER_PAGE
    end_idx = start_idx + PER_PAGE
    page_files = results[start_idx:end_idx]
    
    for file in page_files:
        size_str = format_size(file.get('file_size', 0))
        btn_text = f"{size_str} • {file['file_name']}"
        buttons.append([InlineKeyboardButton(btn_text, callback_data=f"file#{file['file_id']}")])
        
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⏪ Previous", callback_data=f"page#{query}#{page-1}"))
    nav_buttons.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="pages_count"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("Next ⏭️", callback_data=f"page#{query}#{page+1}"))
        
    if nav_buttons:
        buttons.append(nav_buttons)
        
    return InlineKeyboardMarkup(buttons)

# 6. /start Handler (Verification & Direct File Delivery)
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message: Message):
    await db_instance.add_user(message.from_user.id)
    
    if len(message.command) > 1:
        param = message.command[1]
        
        # 24hr Token Verification Completion
        if param.startswith("verify_"):
            await db_instance.set_user_verified(message.from_user.id)
            await message.reply_text("🎉 **24-Hours Verification Successful!**\nAb aap 24 ghante tak direct sabhi files download kar sakte hain.")
            return

        # Direct File Delivery via Poster Button
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

    # Force Subscription Validation
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

# 7. Channel Auto-Post with TMDb Hyperlink & Small-Caps Button Font
@app.on_message(filters.chat(CHANNELS) & (filters.document | filters.video | filters.audio))
async def media_indexer(client, message: Message):
    media = message.document or message.video or message.audio
    if media:
        file_name = getattr(media, "file_name", None) or message.caption or "Unknown Movie"
        file_data = {
            "file_id": media.file_id,
            "file_name": file_name,
            "file_size": media.file_size,
            "mime_type": getattr(media, "mime_type", "")
        }
        await db_instance.save_file(file_data)

        if AUTO_POST and UPDATE_CHANNEL:
            meta = await fetch_tmdb_metadata(file_name)
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

# 8. User Search Filter
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
    
    reply_markup = create_search_markup(results, query, page=1)
    await message.reply_text(
        text=f"Title : <b>{query.title()}</b>\nYour Files are Ready Now",
        reply_markup=reply_markup,
        quote=True
    )

# 9. Pagination Callback
@app.on_callback_query(filters.regex(r"^page#"))
async def pagination_handler(client, query: CallbackQuery):
    data_parts = query.data.split("#")
    search_query = data_parts[1]
    page_num = int(data_parts[2])
    
    results = await db_instance.search_media(search_query)
    if not results:
        await query.answer("❌ Koi file nahi mili!", show_alert=True)
        return
        
    reply_markup = create_search_markup(results, search_query, page=page_num)
    try:
        await query.message.edit_reply_markup(reply_markup=reply_markup)
    except Exception:
        pass
    await query.answer()

# 10. File Delivery Callback & 24hr Token Check
@app.on_callback_query(filters.regex(r"^file#"))
async def send_file_handler(client, query: CallbackQuery):
    user_id = query.from_user.id
    if not await is_subscribed(client, user_id):
        await query.answer("⚠️ Pehle update channel join karein!", show_alert=True)
        return

    if USE_SHORTLINK and not await db_instance.is_user_verified(user_id):
        token = str(uuid.uuid4())[:8]
        verify_url = await get_shortlink(f"https://t.me/{BOT_USERNAME}?start=verify_{token}")
        btn = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔓 Verify 24hr Access Token", url=verify_url)
        ]])
        await query.message.reply_text(
            "⚠️ **24-Ghante ka Access Token Expire ho gaya!**\n\nNiche diye link se ek baar token verify karein, fir 24 ghante sabhi movies direct download karein.",
            reply_markup=btn
        )
        return
    
    file_id = query.data.split("#", 1)[1]
    caption = Script.CUSTOM_FILE_CAPTION.format(file_name="Requested Video", file_size="HD", bot_username=BOT_USERNAME)
    await client.send_cached_media(chat_id=user_id, file_id=file_id, caption=caption)
    await query.answer("✅ File bhej di gayi hai!", show_alert=True)

# 11. Subscription Check & Admin Stats Handlers
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
