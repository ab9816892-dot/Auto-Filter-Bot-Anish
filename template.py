class Script:
    START_TEXT = "Hello **{}**!\n\nMain ek Advanced Auto-Filter Movie Bot hoon. Mujhe apne movie channel me Admin banayein aur group me movies search karein!"
    
    FORCE_SUB_TEXT = "<b>⚠️ Access Denied!</b>\n\nMovie file lene ke liye aapko hamare update channel ko join karna zaroori hai. Channel join karne ke baad niche **'🔄 Try Again'** button par click karein."

    # 100% Exact Same-to-Same Small-Caps Font & Blockquote Template
    POST_TEMPLATE = """
📩 [NEW #{media_type} ADDED]({tmdb_url})

✨ **ᴛɪᴛʟᴇ :** `{title}`
━━━━━━✦━━━━━━
> 🎭 **ɢᴇɴʀᴇs :** {genres}
> 🍿 **ᴏᴛᴛ    :** {ott}
> 🎬 **ǫᴜᴀʟɪᴛʏ :** 1080p, 720p, web-dl
> 🎧 **ᴀᴜᴅɪᴏ  :** Multi Audio
> 🌟 **ʀᴀᴛɪɴɢ :** {rating}
> 📺 **ᴇᴘɪsᴏᴅᴇs :** {episodes}
━━━━━━✦━━━━━━
🔍 **ꜱᴇᴀʀᴄʜ ➔** [{bot_name}](https://t.me/{bot_username}) 🔍
"""

    # Tap-to-copy mono format for universal file caption
    CUSTOM_FILE_CAPTION = """🎬 **`{file_name}`**

📦 **Size :** `{file_size}`
🎧 **Audio :** Multi / Dual Audio
🌟 **Channel :** @{bot_username}"""
