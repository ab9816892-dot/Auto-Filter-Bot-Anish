import os
import re
import time
import uuid
import asyncio
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import config
from template import POST_TEMPLATE, CUSTOM_FILE_CAPTION
from database import save_file, get_search_results, is_user_verified, set_user_verified

app = Client(
    "auto_filter_bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

# 1. Title theke Junk / Baje words clean kora
def clean_file_title(filename):
    clean = re.sub(r"(@\w+|\[.*?\]|\(.*?\)|www\.\w+\.\w+|https?://\S+)", "", filename)
    clean = re.sub(r"(1080p|720p|480p|2160p|4k|HEVC|x264|x265|HDRip|HDTV|WEB-DL|BluRay|AAC|ESub|Dual|Multi)", "", clean, flags=re.IGNORECASE)
    clean = clean.replace(".", " ").replace("_", " ").replace("-", " ")
    return " ".join(clean.split())

# 2. Async TMDb Poster & Metadata Fetch
async def fetch_tmdb_metadata(query):
    clean_name = clean_file_title(query)
    search_term = " ".join(clean_name.split()[:3])
    url = f"https://api.themoviedb.org/3/search/multi?api_key={config.TMDB_API_KEY}&query={search_term}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                if data.get("results"):
                    res = data["results"][0]
                    title = res.get("title") or res.get("name") or search_term
                    poster_path = res.get("poster_path")
                    poster = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else "https://envs.sh/default_poster.jpg"
                    rating = res.get("vote_average", "8.5")
                    media_type = res.get("media_type", "movie").upper()
                    return {"title": title, "poster": poster, "rating": rating, "type": media_type}
    except Exception:
        pass
    return {
        "title": search_term.title(),
        "poster": "https://envs.sh/default_poster.jpg",
        "rating": "8.5",
        "type": "SERIES"
    }

# 3. Shortlink Generator
async def get_shortlink(long_url):
    api_url = f"https://{config.SHORTLINK_URL}/api?api={config.SHORTLINK_API}&url={long_url}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as resp:
                data = await resp.json()
                return data.get("shortenedUrl", long_url)
    except Exception:
        return long_url

# 4. Target Channel Auto-Index & Auto-Post
@app.on_message(filters.chat(config.CHANNELS) & (filters.video | filters.document))
async def auto_index_channel(client, message):
    media = message.video or message.document
    if not media or not getattr(media, "file_name", None):
        return

    # MongoDB Save
    await save_file(media)

    # TMDb Auto-Poster to Update Channel
    if config.AUTO_POST and config.UPDATE_CHANNEL:
        meta = await fetch_tmdb_metadata(media.file_name)
        caption = POST_TEMPLATE.format(
            media_type=meta["type"],
            title=meta["title"],
            rating=meta["rating"],
            bot_username=config.BOT_USERNAME
        )
        btn = InlineKeyboardMarkup([[
            InlineKeyboardButton("🚀 GET FILES", url=f"https://t.me/{config.BOT_USERNAME}?start=getfile_{media.file_id}")
        ]])
        try:
            await client.send_photo(
                chat_id=config.UPDATE_CHANNEL,
                photo=meta["poster"],
                caption=caption,
                reply_markup=btn
            )
        except Exception as e:
            print(f"Update channel auto-post error: {e}")

# 5. User PM Search
@app.on_message(filters.text & filters.private & ~filters.command(["start", "help"]))
async def pm_search(client, message):
    query = message.text.strip()
    files = await get_search_results(query)
    if not files:
        await message.reply_text("❌ Kono file pawa jayni! Correct spelling likhe abar search koro.")
        return

    buttons = []
    for f in files:
        size_mb = round(f["file_size"] / (1024 * 1024), 1)
        btn_text = f"🎬 {f['file_name']} [{size_mb} MB]"
        buttons.append([InlineKeyboardButton(btn_text, callback_data=f"file_{f['_id']}")])

    await message.reply_text(
        f"🔍 Results for: **{query}**",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# 6. Button Callback & 24hr Verification
@app.on_callback_query(filters.regex(r"^file_"))
async def send_file_callback(client, callback_query):
    file_id = callback_query.data.split("_", 1)[1]
    user_id = callback_query.from_user.id

    if config.USE_SHORTLINK and not await is_user_verified(user_id):
        token = str(uuid.uuid4())[:8]
        verify_url = await get_shortlink(f"https://t.me/{config.BOT_USERNAME}?start=verify_{token}")
        btn = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔓 Verify 24hr Access Token", url=verify_url)
        ]])
        await callback_query.message.reply_text(
            "⚠️ **24-Ghontar Access Token Expired!**\n\nNicher link theke ekbar verify kore nao, tarpor 24 ghonta sob movie direct download korte parbe.",
            reply_markup=btn
        )
        return

    caption = CUSTOM_FILE_CAPTION.format(
        file_name="Requested File",
        file_size="HD",
        bot_username=config.BOT_USERNAME
    )
    try:
        await client.send_cached_media(chat_id=user_id, file_id=file_id, caption=caption)
        await callback_query.answer("✅ File sent!")
    except Exception as e:
        await callback_query.answer(f"Error: {e}", show_alert=True)

# 7. /start Handler
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    if len(message.command) > 1:
        param = message.command[1]

        # Verification Callback
        if param.startswith("verify_"):
            await set_user_verified(message.from_user.id)
            await message.reply_text("🎉 **Verification Successful!**\nNext 24 ghonta sob files direct download korte parbe.")
            return

        # Direct File Fetch from Auto-Post
        if param.startswith("getfile_"):
            file_id = param.split("_", 1)[1]
            if config.USE_SHORTLINK and not await is_user_verified(message.from_user.id):
                token = str(uuid.uuid4())[:8]
                verify_url = await get_shortlink(f"https://t.me/{config.BOT_USERNAME}?start=verify_{token}")
                btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔓 Verify Access Token", url=verify_url)]])
                await message.reply_text("⚠️ File download korar age 24hr token verify koro:", reply_markup=btn)
                return

            caption = CUSTOM_FILE_CAPTION.format(file_name="Requested File", file_size="HD", bot_username=config.BOT_USERNAME)
            await client.send_cached_media(chat_id=message.from_user.id, file_id=file_id, caption=caption)
            return

    await message.reply_text(f"👋 Hey {message.from_user.mention},\nMovie ba Anime-r name likhe search koro!")

print("🚀 Bot starting...")
app.run()
