from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shivu import shivuu, collection, user_collection, group_user_totals_collection
import asyncio

async def get_user_collection():
    return await user_collection.find({}).to_list(length=None)

async def get_progress_bar(user_waifus_count, total_waifus_count):
    current = user_waifus_count
    total = total_waifus_count
    bar_width = 10

    progress = current / total if total != 0 else 0
    progress_percent = progress * 100

    filled_width = int(progress * bar_width)
    empty_width = bar_width - filled_width

    progress_bar = "▰" * filled_width + "▱" * empty_width
    status = f"{progress_bar}"
    return status, progress_percent

async def get_chat_top(chat_id: int, user_id: int) -> int:
    pipeline = [
        {"$match": {"group_id": chat_id}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    cursor = group_user_totals_collection.aggregate(pipeline)
    leaderboard_data = await cursor.to_list(length=None)
    
    for i, user in enumerate(leaderboard_data, start=1):
        if user.get('user_id') == user_id:
            return i
    
    return 0

async def get_global_top(user_id: int) -> int:
    pipeline = [
        {"$project": {"id": 1, "characters_count": {"$size": {"$ifNull": ["$characters", []]}}}},
        {"$sort": {"characters_count": -1}}
    ]
    cursor = user_collection.aggregate(pipeline)
    leaderboard_data = await cursor.to_list(length=None)
    
    for i, user in enumerate(leaderboard_data, start=1):
        if user.get('id') == user_id:
            return i
    
    return 0

@shivuu.on_message(filters.command(["myprofile"]))
async def send_grabber_status(client, message):
    try:
        # Show loading animation with percentage
        loading_message = await message.reply("▒▒▒▒▒▒▒▒▒▒ 0% ᴄᴏᴍᴘʟᴇᴛᴇ!")

        for i in range(90, 101):
            await asyncio.sleep(0.01)  # Adjust speed of progress here
            await loading_message.edit_text(f"▒▒▒▒▒▒▒▒▒▒ {i}% ᴄᴏᴍᴘʟᴇᴛᴇ!")

        user_collection_data = await get_user_collection()
        user_collection_count = len(user_collection_data)

        user_id = message.from_user.id
        user = await user_collection.find_one({'id': user_id})

        if user:
            total_count = len(user.get('characters', []))
        else:
            total_count = 0

        total_waifus_count = await collection.count_documents({})

        chat_top = await get_chat_top(message.chat.id, user_id)
        global_top = await get_global_top(user_id)

        progress_bar, progress_percent = await get_progress_bar(total_count, total_waifus_count)

        grabber_status = (
            f"╒════「𝗨𝗦𝗘𝗥 𝗣𝗥𝗢𝗙𝗜𝗟𝗘」\n"
            f"╰─➩ ᴜsᴇʀ: `{message.from_user.first_name}`\n"
            f"╰─➩ ᴜsᴇʀ ɪᴅ: `{message.from_user.id}`\n"
            f"╰─➩ ᴛᴏᴛᴀʟ ʜᴜꜱʙᴀɴᴅᴏ: `{total_count}`\n"
            f"╰─➩ ʜᴀʀᴇᴍ: `{total_count}/{total_waifus_count}` ({progress_percent:.3f}%)\n"
            f"╰─➩ ʙᴀʀ: {progress_bar}\n"
            f"╰   ╰─➩ {progress_percent:.2f}% Complete\n"
            f"╭──────────────────\n"
            f"├─➩ 🌍  𝘾𝙃𝘼𝙏 𝙏𝙊𝙋 : `{chat_top}`\n"
            f"├─➩ 🌎  𝙂𝙇𝙊𝘽𝘼𝙇 𝙏𝙊𝙋 : `{global_top}`\n"
            f"╰──────────────────"
        )

        user_photo = await client.download_media(message.from_user.photo.big_file_id)

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("sᴇᴇ ᴄᴏʟʟᴇᴄᴛɪᴏɴ", switch_inline_query_current_chat=f"collection.{user_id}")]
        ])

        await client.send_photo(
            chat_id=message.chat.id,
            photo=user_photo,
            caption=grabber_status,
            reply_markup=keyboard,
        )

        # Delete the loading message after sending the actual response
        await loading_message.delete()

    except Exception as e:
        await message.reply(f"An error occurred: {e}")
