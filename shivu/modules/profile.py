import os
import html
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from shivu import application, user_collection, collection

async def get_global_rank(username: str) -> int:
    pipeline = [
        {"$match": {"characters": {"$exists": True, "$ne": []}}},
        {"$project": {"username": 1, "character_count": {"$size": "$characters"}}},
        {"$sort": {"character_count": -1}}
    ]
    cursor = user_collection.aggregate(pipeline)
    leaderboard_data = await cursor.to_list(length=None)
    total_users = await user_collection.count_documents({})
    for i, user in enumerate(leaderboard_data, start=1):
        if user.get('username') == username:
            return i, total_users
    return 0, total_users

async def my_profile(update: Update, context: CallbackContext):
    if update.message:
        # Animated loading message
        loading_message = await context.bot.send_message(
            chat_id=update.message.chat_id,
            text="⏳ **Fetching your profile...**",
            parse_mode="Markdown"
        )
        await asyncio.sleep(2)

        user_id = update.effective_user.id
        user_data = await user_collection.find_one({'id': user_id})

        if user_data:
            # User details
            user_first_name = user_data.get('first_name', 'Unknown')
            user_username = user_data.get('username', 'Unknown')
            total_characters = await collection.count_documents({})
            characters = user_data.get('characters', [])
            characters_count = len(characters)
            character_percentage = (characters_count / total_characters) * 100 if total_characters > 0 else 0

            # Get rarity counts from user's collection
            rarity_counts = {}
            for char in characters:
                rarity = char.get('rarity', '🔵 𝙇𝙊𝙒')
                rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1

            rarity_message = "\n".join([
                f"⌠{rarity.split()[0]}⌡ Rarity: {' '.join(rarity.split()[1:])}: {count}"
                for rarity, count in rarity_counts.items()
            ])

            # Global rank
            global_rank, total_users = await get_global_rank(user_username)

            # Progress bar
            progress_bar_length = 10
            filled_blocks = int((character_percentage / 100) * progress_bar_length)
            progress_bar = "▰" * filled_blocks + "▱" * (progress_bar_length - filled_blocks)

            # Profile details
            profile_pic_url = "https://files.catbox.moe/m549da.jpg"
            user_tag = f"<a href='tg://user?id={user_id}'>{html.escape(user_first_name)}</a>"
            profile_message = (
                f"╭── ˹ ɪɴғᴏʀᴍᴀᴛɪᴏɴ ˼ ──•\n"
                f"┆\n"
                f"┊◍ ɴᴀᴍᴇ: {user_tag}\n"
                f"┆◍ ᴛᴏᴛᴀʟ ᴡᴀɪғᴜs ɪɴ ʙᴏᴛ: {total_characters}\n"
                f"┊● ᴜsᴇʀ ᴄʜᴀʀᴀᴄᴛᴇʀs : {characters_count} ({character_percentage:.2f}%)\n"
                f"┆● ᴅᴇᴠᴇʟᴏᴘᴍᴇɴᴛ ʙᴀʀ: {progress_bar}\n\n"
                f"┆● ɢʟᴏʙᴀʟ ʀᴀɴᴋ: {global_rank} / {total_users}\n"
                f"├─────────────────•\n"
                f"┆   ❖ │ ʀᴀʀɪᴛʏ ᴄᴏᴜɴᴛ │ ❖\n"
                f"├─────────────────•\n"
                f"{rarity_message}\n"
                f"╰─────────────────•"
            )

            close_button = InlineKeyboardButton("ᴄʟᴏsᴇ 🔖", callback_data="close")
            keyboard = InlineKeyboardMarkup([[close_button]])

            # Edit loading message with profile and delete loading message
            try:
                await context.bot.edit_message_text(
                    chat_id=loading_message.chat_id,
                    message_id=loading_message.message_id,
                    text="🎉 **Profile Loaded!**",
                    parse_mode="Markdown"
                )
                await context.bot.send_photo(
                    chat_id=update.message.chat_id,
                    photo=profile_pic_url,
                    caption=profile_message,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            except Exception as e:
                print(f"Error in sending profile: {e}")
        else:
            await loading_message.edit_text("❌ Unable to retrieve user information.")
    else:
        print("No message to reply to.")

application.add_handler(CommandHandler("myprofile", my_profile))

async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    if query.data == "close":
        try:
            await query.message.delete()
        except Exception as e:
            print(f"Error in deleting message: {e}")
    await query.answer()

application.add_handler(CallbackQueryHandler(button))
