import random
from html import escape
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler

from shivu import application, PHOTO_URL, SUPPORT_CHAT, UPDATE_CHAT, BOT_USERNAME, db, GROUP_ID
from shivu import user_collection, refeer_collection

async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    username = update.effective_user.username
    args = context.args
    referring_user_id = None
    
    if args and args[0].startswith('r_'):
        referring_user_id = int(args[0][2:])

    user_data = await user_collection.find_one({"id": user_id})

    if user_data is None:
        new_user = {"id": user_id, "first_name": first_name, "username": username, "tokens": 500, "characters": []}
        await user_collection.insert_one(new_user)

        if referring_user_id:
            referring_user_data = await user_collection.find_one({"id": referring_user_id})
            if referring_user_data:
                await user_collection.update_one({"id": referring_user_id}, {"$inc": {"tokens": 1000}})
                referrer_message = f"{first_name} referred you and you got 1000 tokens!"
                try:
                    await context.bot.send_message(chat_id=referring_user_id, text=referrer_message)
                except Exception as e:
                    print(f"Failed to send referral message: {e}")
        
        await context.bot.send_message(chat_id=GROUP_ID, 
                                       text=f"We Got New User \n#NEWUSER\n User: <a href='tg://user?id={user_id}'>{escape(first_name)}</a>", 
                                       parse_mode='HTML')
    else:
        if user_data['first_name'] != first_name or user_data['username'] != username:
            await user_collection.update_one({"id": user_id}, {"$set": {"first_name": first_name, "username": username}})

    if update.effective_chat.type == "private":
        caption = f"""
╭────── ˹ ɢʀᴇᴇᴛɪɴɢs ˼ ──────•
┆
┊◍ ʜᴇʏ : {first_name} 
┆◍ ɪ ᴀᴍ : [ɢʀᴀᴘ ʏᴏᴜʀ ᴡᴀɪғᴜ](https://t.me/Grap_Waifu_Bot)
┊● ɪ ᴀᴍ ᴀɴɪᴍᴇ ʙᴀsᴇᴅ ɢᴀᴍᴇ ʙᴏᴛ! 
├───────˹ ɪɴғᴏʀᴍᴀᴛɪᴏɴ ˼──────•
┆
┆① ᴡᴀɪғᴜ ɢʀᴀᴘ ʙᴏᴛ ᴡɪʟʟ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ sᴘᴀᴡɴ ᴀ ɴᴇᴡ ᴡᴀɪғᴜ ɪɴ ʏᴏᴜʀ ᴄʜᴀᴛ ᴀғᴛᴇʀ ᴇᴠᴇʀʏ 100 ᴍᴇssᴀɢᴇs ʙʏ ᴅᴇғᴀᴜʟᴛ.
┆② ʏᴏᴜ ᴄᴀɴ ᴀʟsᴏ ᴄᴜsᴛᴏᴍɪᴢᴇ ᴛʜᴇ sᴘᴀᴡɴ ʀᴀᴛᴇ ᴀɴᴅ ᴏᴛʜᴇʀ sᴇᴛᴛɪɴɢs ᴛᴏ ʏᴏᴜʀ ʟɪᴋɪɴɢ.
┆③ ʜᴏᴡ ᴛᴏ ᴜsᴇ ᴍᴇ:
sɪᴍᴘʟʏ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ.
┆
├──────────────────────•
┆    ❖ │ ɢʀᴀᴘ ʏᴏᴜʀ ᴡᴀɪғᴜ │ ❖
├──────────────────────•
┆● ʙᴏᴛ ᴜᴘᴅᴀᴛᴇs - [ɢʀᴀᴘ ᴜᴘᴅᴀᴛᴇs](https://t.me/dynamic_bot_supports)
┊● ʙᴏᴛ sᴜᴘᴘᴏʀᴛ - [ᴅʏɴᴀᴍɪᴄ ɢᴀɴɢs](https://t.me/main_dynamic)
╰──────────────────────•"""
        
        keyboard = [
            [InlineKeyboardButton("❖ Λᴅᴅ ᴍᴇ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ ❖", url=f'https://t.me/Grap_Waifu_Bot?startgroup=new')],
            [InlineKeyboardButton("● sᴜᴘᴘᴏʀᴛ ●", url=f'https://t.me/main_dynamic'),
            InlineKeyboardButton("● ᴜᴘᴅᴀᴛᴇ ●", url=f'https://t.me/dynamic_bot_supports')],
            [InlineKeyboardButton("● ғᴀǫ ●", url=f'https://telegra.ph/Seizer-Faq-Menu-09-05')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        video_url = "https://files.catbox.moe/mnnsi1.mp4"
        sticker_url = "CAACAgUAAxkBAAIbA2cHsEvSH3z-ZXdePQVS-CriXaXyAAI4CAACIO2AVVXo4fgsIMA-NgQ"  # Add sticker URL
        await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker=sticker_url)
        await context.bot.send_video(chat_id=update.effective_chat.id, video=video_url, caption=caption, reply_markup=reply_markup, parse_mode='markdown')
    else:
        photo_url = random.choice(PHOTO_URL)
        keyboard = [
            [InlineKeyboardButton("PM", url=f'https://t.me/Grap_Waifu_Bot?start=true')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        video_url = "https://telegra.ph/file/43e42d98cf6820892cf47.mp4"
        await context.bot.send_video(chat_id=update.effective_chat.id, video=video_url, caption=f"""𝙃𝙚𝙮 𝙩𝙝𝙚𝙧𝙚! {first_name}\n\n✨𝙄 𝘼𝙈 𝘼𝙡𝙞𝙫𝙚 𝘽𝙖𝙗𝙮""", reply_markup=reply_markup)

start_handler = CommandHandler('start', start, block=False)
application.add_handler(start_handler)
