import os
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from config import (
    API_ID, API_HASH, BOT_TOKEN, BOT_USERNAME, ADMINS,
    CHANNELS, FORCE_SUB_CHANNEL, UPDATE_CHANNEL, LOG_CHANNEL,
    MAX_RESULTS
)
from database import db_instance

# ==========================================
# TOMAR BANANO CUSTOM START IMAGE BANNER
# ==========================================
START_PIC = "https://i.ibb.co/PZtMPSKf/boultflix-popcorn-cart.webp"

# Initialize Pyrogram Client
app = Client(
    "BoultFlixBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ==========================================
# /START HANDLER (RPEDITZ STYLE + BANNER)
# ==========================================
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    user = message.from_user
    await db_instance.add_user(user.id, user.first_name)
    
    # Direct File Link Handler (e.g., /start file_xxx)
    if len(message.command) > 1:
        data = message.command[1]
        if data.startswith("file_"):
            file_id = data.split("file_")[1]
            file_data = await db_instance.get_file(file_id)
            if file_data:
                try:
                    caption = file_data.get("caption") or f"<b>🎬 {file_data.get('file_name', 'File')}</b>"
                    await client.send_cached_media(
                        chat_id=message.chat.id,
                        file_id=file_data["file_id"],
                        caption=caption
                    )
                    return
                except Exception:
                    await message.reply_text("❌ File pathate somoshya hoyeche ba file delete hoye geche.")
                    return
            else:
                await message.reply_text("❌ File khuje pawa jayni!")
                return

    caption = (
        f"Hey 🍿 <b>{user.mention}</b> 🥷\n\n"
        f"📍 <b>Welcome To The World's Coolest Search Engine!</b>\n\n"
        f"Here You Can Request Movie's, Just Sent Movie OR WebSeries Name With Proper <b>Google Spelling</b>..!!"
    )
    
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ ADD ME TO YOUR GROUP ➕", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")
        ],
        [
            InlineKeyboardButton("📑 HELP", callback_data="help_btn"),
            InlineKeyboardButton("ℹ️ ABOUT", callback_data="about_btn")
        ],
        [
            InlineKeyboardButton("🌟 TOP SEARCHING 🌟", callback_data="top_search_btn")
        ]
    ])
    
    try:
        await message.reply_photo(
            photo=START_PIC,
            caption=caption,
            reply_markup=buttons
        )
    except Exception:
        await message.reply_text(
            text=caption,
            reply_markup=buttons
        )

# ==========================================
# CALLBACK HANDLERS (BUTTON CLICKS)
# ==========================================
@app.on_callback_query()
async def callback_handler(client: Client, query: CallbackQuery):
    data = query.data
    
    if data == "help_btn":
        text = (
            "<b>📑 Bot Help & Usage Guide</b>\n\n"
            "• Direct chat ba connected group-e movie/series-er shothik naam likhe pathao.\n"
            "• Bot sathe sathe download button pathiye debe.\n"
            "• Google spelling use koro file accurately pete."
        )
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="home_btn")]])
        await query.message.edit_text(text, reply_markup=btn)
        
    elif data == "about_btn":
        admin_id = ADMINS[0] if ADMINS else 7067885693
        text = (
            f"<b>ℹ️ About This Bot</b>\n\n"
            f"• <b>Name:</b> @{BOT_USERNAME}\n"
            f"• <b>Developer / Owner:</b> <a href='tg://user?id={admin_id}'>Owner</a>\n"
            f"• <b>Language:</b> Python 3\n"
            f"• <b>Framework:</b> Pyrogram / Pyrofork\n"
            f"• <b>Database:</b> MongoDB"
        )
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="home_btn")]])
        await query.message.edit_text(text, reply_markup=btn)
        
    elif data == "top_search_btn":
        text = "<b>🌟 Currently Trending Searches</b>\n\n<i>Directly movie ba series er naam send koro files pete!</i>"
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="home_btn")]])
        await query.message.edit_text(text, reply_markup=btn)
        
    elif data == "home_btn":
        caption = (
            f"Hey 🍿 <b>{query.from_user.mention}</b> 🥷\n\n"
            f"📍 <b>Welcome To The World's Coolest Search Engine!</b>\n\n"
            f"Here You Can Request Movie's, Just Sent Movie OR WebSeries Name With Proper <b>Google Spelling</b>..!!"
        )
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("➕ ADD ME TO YOUR GROUP ➕", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")
            ],
            [
                InlineKeyboardButton("📑 HELP", callback_data="help_btn"),
                InlineKeyboardButton("ℹ️ ABOUT", callback_data="about_btn")
            ],
            [
                InlineKeyboardButton("🌟 TOP SEARCHING 🌟", callback_data="top_search_btn")
            ]
        ])
        try:
            await query.message.edit_text(caption, reply_markup=buttons)
        except Exception:
            pass
            
    elif data.startswith("getfile_"):
        file_id = data.split("getfile_")[1]
        file_data = await db_instance.get_file(file_id)
        if not file_data:
            await query.answer("❌ File khuje pawa jayni!", show_alert=True)
            return
        try:
            caption = file_data.get("caption") or f"<b>🎬 {file_data.get('file_name', 'File')}</b>"
            await client.send_cached_media(
                chat_id=query.message.chat.id,
                file_id=file_data["file_id"],
                caption=caption
            )
            await query.answer("✅ File sent!")
        except Exception:
            await query.answer("❌ File send failed!", show_alert=True)

# ==========================================
# AUTO INDEX FILES FROM STORAGE CHANNELS
# ==========================================
@app.on_message(filters.channel & (filters.document | filters.video | filters.audio))
async def channel_indexer(client: Client, message: Message):
    if message.chat.id in CHANNELS:
        media = message.document or message.video or message.audio
        media.caption = message.caption.html if message.caption else ""
        await db_instance.save_file(media)

# ==========================================
# MOVIE SEARCH HANDLER (PM & GROUP)
# ==========================================
@app.on_message(filters.text & ~filters.command(["start", "help", "about"]))
async def search_handler(client: Client, message: Message):
    query = message.text.strip()
    if len(query) < 2:
        return
    
    results, total = await db_instance.get_search_results(query, max_results=MAX_RESULTS)
    
    if not results:
        await message.reply_text(
            f"❌ <b>'{query}'</b> er kono result pawa jayni!\n\n"
            f"👉 Google spelling check kore abar try koro."
        )
        return
    
    buttons = []
    for file in results:
        file_name = file.get("file_name", "Download")
        file_id = file.get("file_id")
        btn_text = f"🎬 {file_name[:40]}..." if len(file_name) > 42 else f"🎬 {file_name}"
        buttons.append([InlineKeyboardButton(btn_text, callback_data=f"getfile_{file_id}")])
    
    await message.reply_text(
        f"🔍 <b>Results for:</b> <code>{query}</code>\n"
        f"📁 <b>Total Files Found:</b> {total}\n\n"
        f"👇 Nicher button-e click kore file download koro:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

if __name__ == "__main__":
    print("--- BoultFlix Movie Bot Started Successfully ---")
    app.run()
