import os
import random
import asyncio
import urllib.parse
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import API_ID, API_HASH, BOT_TOKEN, BOT_USERNAME, ADMINS, CHANNELS
from database import db_instance

logging.basicConfig(level=logging.INFO)

# Banner Poster Link (High-Speed JPG)
START_PIC = "https://i.ibb.co/PZtMPSKf/boultflix-popcorn-cart.webp"

# Channel & Support Links
UPDATES_CHANNEL_URL = "https://t.me/+f-k01NScSxEyNzc1"
SUPPORT_BOT_URL = "https://t.me/BoultFlixSupportBot"

# Reaction Emojis
REACTION_EMOJIS = [
    "🔥", "⚡", "❤️", "🍿", "🥰", "🎉", "🤩", "👏", 
    "👌", "🕊️", "😍", "💯", "💖", "🍓", "🍾", "😎", 
    "👾", "✨", "🤙", "🥂", "🎬", "🏆", "💎", "👻", 
    "🚀", "👑", "🫡", "🤝", "💫", "🌟"
]

app = Client(
    "BoultFlixMovieBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

async def send_reaction(message):
    try:
        await message.react(emoji=random.choice(REACTION_EMOJIS))
    except Exception:
        pass

# ==========================================
# 1. /START HANDLER (INSTANT & NON-BLOCKING)
# ==========================================
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    asyncio.create_task(send_reaction(message))

    user = message.from_user
    asyncio.create_task(db_instance.add_user(user.id, user.first_name))
    
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
# 2. ULTRA-FAST PARALLEL INDEXER ENGINE
# ==========================================
async def run_fast_indexing(client, status_msg, target_chat, max_id):
    total_indexed = 0
    batch_size = 200
    last_update_id = 0

    # Scanning from 1 to latest ID
    for start_id in range(1, max_id + 1, batch_size):
        id_list = list(range(start_id, min(start_id + batch_size, max_id + 1)))
        
        try:
            messages = await client.get_messages(target_chat, message_ids=id_list)
        except Exception:
            await asyncio.sleep(0.5)
            continue

        db_tasks = []
        for msg in messages:
            if not msg:
                continue

            media = msg.video or msg.document
            if not media:
                continue

            # 100MB Size Filter
            if getattr(media, "file_size", 0) >= (100 * 1024 * 1024):
                db_tasks.append(db_instance.save_file(media))

        # Parallel Batch Save to MongoDB
        if db_tasks:
            results = await asyncio.gather(*db_tasks, return_exceptions=True)
            saved_count = sum(1 for r in results if not isinstance(r, Exception))
            total_indexed += saved_count

        # Update UI every 2000 messages
        if (start_id - last_update_id) >= 2000 or (start_id + batch_size) > max_id:
            percentage = round((min(start_id + batch_size - 1, max_id) / max_id) * 100, 1)
            try:
                await status_msg.edit_text(
                    f"⚡ <b>Iɴᴅᴇxɪɴɢ Iɴ Pʀᴏɢʀᴇss ({percentage}%)...</b>\n\n"
                    f"📊 <b>Sᴄᴀɴɴᴇᴅ:</b> <code>{min(start_id + batch_size - 1, max_id)}/{max_id}</code>\n"
                    f"📦 <b>Iɴᴅᴇxᴇᴅ Fɪʟᴇs:</b> <code>{total_indexed}</code>\n"
                    f"🚀 <i>Ultra-fast multi-threading active...</i>"
                )
                last_update_id = start_id
            except Exception:
                pass

        await asyncio.sleep(0.1)

    await status_msg.edit_text(
        f"🎉 <b>Iɴᴅᴇxɪɴɢ 100% Cᴏᴍᴘʟᴇᴛᴇ!</b>\n\n"
        f"✅ <b>Tᴏᴛᴀʟ Vɪᴅᴇᴏs Iɴᴅᴇxᴇᴅ:</b> <code>{total_indexed}</code>\n"
        f"⚡ <b>Sᴛᴀᴛᴜs:</b> Search engine fully active & ready!"
    )

@app.on_message(filters.command("index") & filters.private)
async def manual_index_handler(client, message):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        await message.reply_text("⛔ <b>Aᴄᴄᴇss Dᴇɴɪᴇᴅ! Yᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀɴ Aᴅᴍɪɴ.</b>")
        return

    status_msg = await message.reply_text("🔄 <b>Iɴɪᴛɪᴀᴛɪɴɢ Uʟᴛʀᴀ-Fᴀsᴛ Iɴᴅᴇxᴇʀ...</b>")
    target_chat = CHANNELS[0] if CHANNELS else -1004240578315

    try:
        test_msg = await client.send_message(target_chat, "🔄 Calculating IDs...")
        max_id = test_msg.id
        await test_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"❌ <b>Eʀʀᴏʀ:</b> <code>{e}</code>")
        return

    # Run in background task so bot stays 100% responsive
    asyncio.create_task(run_fast_indexing(client, status_msg, target_chat, max_id))

# ==========================================
# 3. CALLBACK HANDLERS
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
            await query.answer("❌ File pathate somossya hoyeche!", show_alert=True)

# ==========================================
# 4. AUTO-FILTER & NO RESULTS HANDLER
# ==========================================
@app.on_message(filters.text & filters.private & ~filters.command(["start", "help", "about", "index"]))
async def search_movie(client, message):
    asyncio.create_task(send_reaction(message))

    query = message.text.strip()
    user = message.from_user
    
    try:
        results, total = await db_instance.get_search_results(query, max_results=10)
    except Exception:
        results, total = [], 0
    
    if not results:
        google_query_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
        
        no_results_text = (
            f"<b>Sᴏʀʀʏ {user.first_name}</b>, <b>ɴᴏ ғɪʟᴇs ᴡᴇʀᴇ ғᴏᴜɴᴅ ғᴏʀ ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ</b> <code>{query}</code> 🙁\n\n"
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
        
    btns = [
        [InlineKeyboardButton(f"📁 {res.get('file_name', 'Download')}", callback_data=f"file_{res.get('file_id', '')}")]
        for res in results
    ]
    await message.reply_text(
        f"🎯 <b>Rᴇsᴜʟᴛs ғᴏʀ:</b> <code>{query}</code>\n⚡ <b>Tᴏᴛᴀʟ ғɪʟᴇs:</b> {total}",
        reply_markup=InlineKeyboardMarkup(btns)
    )

# ==========================================
# 5. REAL-TIME INDEXER (FOR NEW UPLOADS)
# ==========================================
@app.on_message(filters.channel & (filters.document | filters.video | filters.audio))
async def channel_indexer(client, message):
    if message.chat.id in CHANNELS:
        media = message.document or message.video or message.audio
        if media and getattr(media, "file_size", 0) >= (100 * 1024 * 1024):
            await db_instance.save_file(media)

# ==========================================
# 6. MAIN ENTRY POINT
# ==========================================
if __name__ == "__main__":
    app.run()
