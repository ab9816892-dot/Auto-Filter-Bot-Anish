from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import BOT_USERNAME, ADMINS

# Popcorn Cart Banner
START_PIC = "https://i.ibb.co/PZtMPSKf/boultflix-popcorn-cart.webp"

# ==========================================
# 1. /START COMMAND HANDLER
# ==========================================
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    user = message.from_user
    await db_instance.add_user(user.id, user.first_name)
    
    caption = (
        f"Hey 🍿 <b>{user.mention}</b> 🥷\n\n"
        f"📍 <b>Welcome To The World's Coolest Search Engine!</b>\n\n"
        f"Here You Can Request Movie's, Just Sent Movie OR WebSeries Name With Proper <b>Google Spelling</b>..!!"
    )
    
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔰 ADD ME TO YOUR GROUP 🔰", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")
        ],
        [
            InlineKeyboardButton("HELP 📢", callback_data="help_menu"),
            InlineKeyboardButton("ABOUT 📖", callback_data="about_menu")
        ],
        [
            InlineKeyboardButton("TOP SEARCHING ⭐", callback_data="top_search_menu"),
            InlineKeyboardButton("UPGRADE 🎟️", callback_data="upgrade_menu")
        ]
    ])
    
    try:
        await message.reply_photo(photo=START_PIC, caption=caption, reply_markup=buttons)
    except Exception:
        await message.reply_text(text=caption, reply_markup=buttons)

# ==========================================
# 2. ALL BUTTON CALLBACK HANDLERS
# ==========================================
@app.on_callback_query()
async def bot_callbacks(client, query: CallbackQuery):
    data = query.data
    
    # 5th Image: Custom Pop-up Toast
    await query.answer("Share & Support Us ❤️")

    # --- HOME / START MENU ---
    if data == "home_menu":
        caption = (
            f"Hey 🍿 <b>{query.from_user.mention}</b> 🥷\n\n"
            f"📍 <b>Welcome To The World's Coolest Search Engine!</b>\n\n"
            f"Here You Can Request Movie's, Just Sent Movie OR WebSeries Name With Proper <b>Google Spelling</b>..!!"
        )
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔰 ADD ME TO YOUR GROUP 🔰", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")
            ],
            [
                InlineKeyboardButton("HELP 📢", callback_data="help_menu"),
                InlineKeyboardButton("ABOUT 📖", callback_data="about_menu")
            ],
            [
                InlineKeyboardButton("TOP SEARCHING ⭐", callback_data="top_search_menu"),
                InlineKeyboardButton("UPGRADE 🎟️", callback_data="upgrade_menu")
            ]
        ])
        try:
            await query.message.edit_caption(caption=caption, reply_markup=buttons)
        except Exception:
            await query.message.edit_text(text=caption, reply_markup=buttons)

    # --- 2nd TXT FILE: HELP MENU ---
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
            [
                InlineKeyboardButton("🚀 REQUEST HERE 🚀", url="https://t.me/BoultFlixSupportBot")
            ],
            [
                InlineKeyboardButton("⇋ BACK ⇋", callback_data="home_menu")
            ]
        ])
        try:
            await query.message.edit_caption(caption=help_text, reply_markup=help_buttons)
        except Exception:
            await query.message.edit_text(text=help_text, reply_markup=help_buttons)

    # --- 3rd IMAGE: ABOUT MENU (HYPERLINKED) ---
    elif data == "about_menu":
        owner_link = f"tg://user?id={ADMINS[0]}" if ADMINS else "https://t.me/BoultFlixSupportBot"
        about_text = (
            "╭─────[ <b>ᴍʏ ᴅᴇᴛᴀɪʟꜱ</b> ]──────⍟\n"
            f"├⍟ <b>ᴍʏ ɴᴀᴍᴇ :</b> <a href='https://t.me/BoultFlixMovieBot'>Bᴏᴜʟᴛғʟɪx Mᴏᴠɪᴇs 🫧🫶🏼</a>\n"
            f"├⍟ <b>ᴅᴇᴠᴇʟᴏᴘᴇʀ :</b> <a href='{owner_link}'>ᴏᴡɴᴇʀ</a>\n"
            "├⍟ <b>ʟɪʙʀᴀʀʏ :</b> <a href='https://github.com/pyrofork/pyrofork'>ᴘʏʀᴏɢʀᴀᴍ</a>\n"
            "├⍟ <b>ʟᴀɴɢᴜᴀɢᴇ :</b> <a href='https://www.python.org'>ᴘʏᴛʜᴏɴ 3</a>\n"
            "├⍟ <b>ᴅᴀᴛᴀʙᴀꜱᴇ :</b> <a href='https://www.mongodb.com'>ᴍᴏɴɢᴏ ᴅʙ</a>\n"
            "├⍟ <b>ʙᴏᴛ ꜱᴇʀᴠᴇʀ :</b> <a href='https://render.com'>ʀᴇɴᴅᴇʀ</a>\n"
            "├⍟ <b>ʙᴜɪʟᴅ ꜱᴛᴀᴛᴜꜱ :</b> v1.4 [ ꜱᴛᴀʙʟᴇ ]\n"
            "╰───────────────⍟"
        )
        about_buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("‼️ DISCLAIMER ‼️", callback_data="disclaimer_menu")
            ],
            [
                InlineKeyboardButton("⇋ BACK ⇋", callback_data="home_menu")
            ]
        ])
        try:
            await query.message.edit_caption(caption=about_text, reply_markup=about_buttons)
        except Exception:
            await query.message.edit_text(text=about_text, reply_markup=about_buttons)

    # --- DISCLAIMER MENU ---
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
            [
                InlineKeyboardButton("⇋ BACK ⇋", callback_data="about_menu")
            ]
        ])
        try:
            await query.message.edit_caption(caption=disclaimer_text, reply_markup=disclaimer_buttons)
        except Exception:
            await query.message.edit_text(text=disclaimer_text, reply_markup=disclaimer_buttons)

    # --- 6th IMAGE: TOP SEARCHES OF THE DAY (2-COLUMN GRID) ---
    elif data == "top_search_menu":
        top_text = "🔥 <b>𝗧𝗢𝗣 𝗦𝗘𝗔𝗥𝗖𝗛𝗘𝗦 𝗢𝗙 𝗧𝗛𝗘 𝗗𝗔𝗬</b> 🔥\n\n<i>Click any title below to search directly:</i>"
        
        # 2-Column Buttons exact match with screenshot
        top_buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Sex", callback_data="top_search#Sex"),
                InlineKeyboardButton("Dhurandhar", callback_data="top_search#Dhurandhar")
            ],
            [
                InlineKeyboardButton("New movie", callback_data="top_search#New movie"),
                InlineKeyboardButton("Movie", callback_data="top_search#Movie")
            ],
            [
                InlineKeyboardButton("War 2", callback_data="top_search#War 2"),
                InlineKeyboardButton("Toxic", callback_data="top_search#Toxic")
            ],
            [
                InlineKeyboardButton("Saiyaara", callback_data="top_search#Saiyaara"),
                InlineKeyboardButton("Stranger things", callback_data="top_search#Stranger things")
            ],
            [
                InlineKeyboardButton("From", callback_data="top_search#From"),
                InlineKeyboardButton("Border 2", callback_data="top_search#Border 2")
            ],
            [
                InlineKeyboardButton("Dhurandhar 2", callback_data="top_search#Dhurandhar 2"),
                InlineKeyboardButton("Coolie", callback_data="top_search#Coolie")
            ],
            [
                InlineKeyboardButton("Kantara", callback_data="top_search#Kantara"),
                InlineKeyboardButton("Mirzapur", callback_data="top_search#Mirzapur")
            ],
            [
                InlineKeyboardButton("2025", callback_data="top_search#2025"),
                InlineKeyboardButton("Dhurandhar The Revenge 2026", callback_data="top_search#Dhurandhar The Revenge 2026")
            ],
            [
                InlineKeyboardButton("⇋ BACK ⇋", callback_data="home_menu")
            ]
        ])
        try:
            await query.message.edit_caption(caption=top_text, reply_markup=top_buttons)
        except Exception:
            await query.message.edit_text(text=top_text, reply_markup=top_buttons)

    # --- TOP SEARCH ITEM CLICK ---
    elif data.startswith("top_search#"):
        keyword = data.split("#")[1]
        results, total = await db_instance.get_search_results(keyword, max_results=10)
        if not results:
            await query.answer(f"🔍 No files found for '{keyword}'!", show_alert=True)
            return
            
        file_btns = [
            [InlineKeyboardButton(f"📁 {res['file_name']}", callback_data=f"file_{res['file_id']}")]
            for res in results
        ]
        file_btns.append([InlineKeyboardButton("⇋ BACK ⇋", callback_data="top_search_menu")])
        
        try:
            await query.message.edit_caption(
                caption=f"🎯 <b>Results for:</b> <code>{keyword}</code>\nFound {total} files:",
                reply_markup=InlineKeyboardMarkup(file_btns)
            )
        except Exception:
            await query.message.edit_text(
                text=f"🎯 <b>Results for:</b> <code>{keyword}</code>\nFound {total} files:",
                reply_markup=InlineKeyboardMarkup(file_btns)
            )

    # --- UPGRADE BUTTON ---
    elif data == "upgrade_menu":
        await query.answer("🎟️ Upgrade / Premium feature is coming soon!", show_alert=True)
