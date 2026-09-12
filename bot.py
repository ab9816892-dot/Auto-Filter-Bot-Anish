import os
import random
import urllib.parse
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import API_ID, API_HASH, BOT_TOKEN, BOT_USERNAME, ADMINS, CHANNELS
from database import db_instance

logging.basicConfig(level=logging.INFO)

# Banner Poster Link
START_PIC = "https://i.ibb.co/PZtMPSKf/boultflix-popcorn-cart.webp"

# Update Channel Link
UPDATES_CHANNEL_URL = "https://t.me/+f-k01NScSxEyNzc1"

# Trending Reactions List
REACTION_EMOJIS = ["🔥", "⚡", "❤️", "👍", "🍿", "🥰", "🎉", "💯"]

app = Client(
    "BoultFlixMovieBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ==========================================
# 1. /START HANDLER (AESTHETIC SMALL-CAPS)
# ==========================================
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    # Auto Reaction
    try:
        await message.react(emoji=random.choice(REACTION_EMOJIS))
    except Exception:
        pass

    user = message.from_user
    await db_instance.add_user(user.id, user.first_name)
    
    caption = (
        f"ʜᴇʏ 🍿 <b>{user.mention}</b> 🥷\n\n"
        f"📍 <b>ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ᴡᴏʀʟᴅ'ꜱ ᴄᴏᴏʟᴇꜱᴛ ꜱᴇᴀʀᴄʜ ᴇɴɢɪɴᴇ! ⚡</b>\n\n"
        f"ʜᴇʀᴇ ʏᴏᴜ ᴄᴀɴ ʀᴇǫᴜᴇꜱᴛ ᴍᴏᴠɪᴇꜱ & ꜱᴇʀɪᴇꜱ, ᴊᴜꜱᴛ ꜱᴇɴᴅ ɴᴀᴍᴇ ᴡɪᴛʜ ᴘʀᴏᴘᴇʀ <b>ɢᴏᴏɢʟᴇ ꜱᴘᴇʟʟɪɴɢ</b>..!! 🫧🎬"
    )
    
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔰 ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ 🔰", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")
        ],
        [
            InlineKeyboardButton("📢 ᴜᴘᴅᴀᴛᴇꜱ ᴄʜᴀɴɴᴇʟ 📢", url=UPDATES_CHANNEL_URL)
        ],
        [
            InlineKeyboardButton("📑 ʜᴇʟᴘ", callback_data="help_menu"),
            InlineKeyboardButton("ℹ️ ᴀʙᴏᴜᴛ", callback_data="about_menu")
        ]
    ])
    
    try:
        await message.reply_photo(photo=START_PIC, caption=caption, reply_markup=buttons)
    except Exception:
        await message.reply_text(text=caption, reply_markup=buttons)

# ==========================================
# 2. CALLBACKS (HELP, ABOUT, DISCLAIMER)
# ==========================================
@app.on_callback_query()
async def bot_callbacks(client, query: CallbackQuery):
    data = query.data
    
    await query.answer("Share & Support Us ❤️")

    if data == "home_menu":
        caption = (
            f"ʜᴇʏ 🍿 <b>{query.from_user.mention}</b> 🥷\n\n"
            f"📍 <b>ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ᴡᴏʀʟᴅ'ꜱ ᴄᴏᴏʟᴇꜱᴛ ꜱᴇᴀʀᴄʜ ᴇɴɢɪɴᴇ! ⚡</b>\n\n"
            f"ʜᴇʀᴇ ʏᴏᴜ ᴄᴀɴ ʀᴇǫᴜᴇꜱᴛ ᴍᴏᴠɪᴇꜱ & ꜱᴇʀɪᴇꜱ, ᴊᴜꜱᴛ ꜱᴇɴᴅ ɴᴀᴍᴇ ᴡɪᴛʜ ᴘʀᴏᴘᴇʀ <b>ɢᴏᴏɢʟᴇ ꜱᴘᴇʟʟɪɴɢ</b>..!! 🫧🎬"
        )
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔰 ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ 🔰", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")
            ],
            [
                InlineKeyboardButton("📢 ᴜᴘᴅᴀᴛᴇꜱ ᴄʜᴀɴɴᴇʟ 📢", url=UPDATES_CHANNEL_URL)
            ],
            [
                InlineKeyboardButton("📑 ʜᴇʟᴘ", callback_data="help_menu"),
                InlineKeyboardButton("ℹ️ ᴀʙᴏᴜᴛ", callback_data="about_menu")
            ]
        ])
        try:
            await query.message.edit_caption(caption=caption, reply_markup=buttons)
        except Exception:
            await query.message.edit_text(text=caption, reply_markup=buttons)

    elif data == "help_menu":
        help_text = (
            "✨ <b>𝗛𝗢𝗪 𝗧𝗢 𝗚𝗘𝗧 𝗠𝗢𝗩𝗜𝗘𝗦,𝗔𝗡𝗜𝗠𝗘,𝗪𝗘𝗕 𝗦𝗘𝗥𝗜𝗘𝗦,𝗘𝗧𝗖</b> ✨\n\n"
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
            [InlineKeyboardButton("🚀 ʀᴇǫᴜᴇꜱᴛ ʜᴇʀᴇ 🚀", url="https://t.me/BoultFlixSupportBot")],
            [InlineKeyboardButton("⇋ ʙᴀᴄᴋ ⇋", callback_data="home_menu")]
        ])
        try:
            await query.message.edit_caption(caption=help_text, reply_markup=help_buttons)
        except Exception:
            await query.message.edit_text(text=help_text, reply_markup=help_buttons)

    elif data == "about_menu":
        about_text = (
            "╭─────[ <b>ᴍʏ ᴅᴇᴛᴀɪʟꜱ</b> 🫧 ]──────⍟\n"
            f"├⍟ <b>ᴍʏ ɴᴀᴍᴇ :</b> <a href='https://t.me/{BOT_USERNAME}'>Bᴏᴜʟᴛғʟɪx Mᴏᴠɪᴇs 🫧🫶🏼</a>\n"
            f"├⍟ <b>ᴅᴇᴠᴇʟᴏᴘᴇʀ :</b> <a href='https://t.me/BoultFlix'>ᴏᴡɴᴇʀ ⚡</a>\n"
            "├⍟ <b>ʟɪʙʀᴀʀʏ :</b> <a href='https://github.com/pyrofork/pyrofork'>ᴘʏʀᴏɢʀᴀᴍ</a>\n"
            "├⍟ <b>ʟᴀɴɢᴜᴀɢᴇ :</b> <a href='https://www.python.org'>ᴘʏᴛʜᴏɴ 3</a>\n"
            "├⍟ <b>ᴅᴀᴛᴀʙᴀꜱᴇ :</b> <a href='https://www.mongodb.com'>ᴍᴏɴɢᴏ ᴅʙ</a>\n"
            "├⍟ <b>ʙᴏᴛ ꜱᴇʀᴠᴇʀ :</b> <a href='https://render.com'>ʀᴇɴᴅᴇʀ</a>\n"
            "├⍟ <b>ʙᴜɪʟᴅ ꜱᴛᴀᴛᴜꜱ :</b> v1.4 [ ꜱᴛᴀʙʟᴇ 🚀 ]\n"
            "╰───────────────⍟"
        )
        about_buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("‼️ ᴅɪꜱᴄʟᴀɪᴍᴇʀ ‼️", callback_data="disclaimer_menu")],
            [InlineKeyboardButton("⇋ ʙᴀᴄᴋ ⇋", callback_data="home_menu")]
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
            [InlineKeyboardButton("⇋ ʙᴀᴄᴋ ⇋", callback_data="about_menu")]
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
            await query.answer("❌ File pathate somossya hoyeche!", show_alert=True)

# ==========================================
# 3. AUTO-FILTER & RPEDITZ NO-RESULTS HANDLER
# ==========================================
@app.on_message(filters.text & filters.private & ~filters.command(["start", "help", "about"]))
async def search_movie(client, message):
    # Instant Random Reaction to user's message
    try:
        await message.react(emoji=random.choice(REACTION_EMOJIS))
    except Exception:
        pass

    query = message.text.strip()
    user = message.from_user
    results, total = await db_instance.get_search_results(query, max_results=10)
    
    # RPEDITZ STYLE NO RESULTS FOUND TEMPLATE
    if not results:
        google_query_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
        
        no_results_text = (
            f"<b>{user.first_name}</b> 🦅❤️\n"
            f"<blockquote><b>{query}</b></blockquote>\n"
            f"<b>SORRY NO FILES WERE FOUND FOR YOUR REQUEST</b> <code>{query}</code> 🙁\n\n"
            f"<b>CHECK YOUR SPELLING IN GOOGLE AND TRY AGAIN</b> 😃\n\n"
            f"📝 <b>MOVIE REQUEST FORMAT</b> 👇\n\n"
            f"⚜️ <b>EXAMPLE :</b> <code>Jawan</code> or <code>Jawan 2023</code>\n\n"
            f"📝 <b>SERIES REQUEST FORMAT</b> 👇\n\n"
            f"⚜️ <b>EXAMPLE :</b> <code>Loki S01</code> or <code>Loki S01E04</code> or <code>Lucifer S03E24</code>\n\n"
            f"🚯 <b>DONT USE ➡️ ':( ! , . /)</b>"
        )
        
        google_btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 CHECK SPELLING ON GOOGLE 🔍", url=google_query_url)]
        ])
        
        await message.reply_text(
            text=no_results_text,
            reply_markup=google_btn,
            disable_web_page_preview=True
        )
        return
        
    btns = [
        [InlineKeyboardButton(f"📁 {res.get('file_name', 'Download')}", callback_data=f"file_{res.get('file_id', '')}")]
        for res in results
    ]
    await message.reply_text(
        f"🎯 <b>ʀᴇꜱᴜʟᴛꜱ ғᴏʀ:</b> <code>{query}</code>\n⚡ <b>ᴛᴏᴛᴀʟ ғɪʟᴇꜱ:</b> {total}",
        reply_markup=InlineKeyboardMarkup(btns)
    )

# ==========================================
# 4. CHANNEL AUTO-INDEXING HANDLER
# ==========================================
@app.on_message(filters.channel & (filters.document | filters.video | filters.audio))
async def channel_indexer(client, message):
    if message.chat.id in CHANNELS:
        media = message.document or message.video or message.audio
        if media:
            await db_instance.save_file(media)

# ==========================================
# 5. MAIN ENTRY POINT
# ==========================================
if __name__ == "__main__":
    app.run()
