from pyrogram import filters, Client, types as t
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shivu import shivuu as bot
from shivu import user_collection, collection
from datetime import datetime, timedelta
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.enums import ChatMemberStatus

DEVS = (6995317382,)  # Developer user IDs
SUPPORT_CHAT_ID = -1002466950912  # ID grup support
CHANNEL_ID = -1002122552289  # ID channel resmi
COMMUNITY_GROUP_ID = -1002466950912  # ID grup community

# Tombol untuk grup support, channel resmi, dan grup community
keyboard_support = t.InlineKeyboardMarkup([
    [t.InlineKeyboardButton("Official Grap group", url="https://t.me/Dyna_community")]
])
keyboard_channel = t.InlineKeyboardMarkup([
    [t.InlineKeyboardButton("Official Grap W/H", url="https://t.me/Seizer_updates")]
])
keyboard_community = t.InlineKeyboardMarkup([
    [t.InlineKeyboardButton("Community Groups", url="https://t.me/Dyna_community")]
])
keyboard_both = t.InlineKeyboardMarkup([
    [t.InlineKeyboardButton("Official Grap W/H Groups", url="https://t.me/Dyna_community")],
    [t.InlineKeyboardButton("Official Grap W/H", url="https://t.me/Seizer_updates")]
])
keyboard_all = t.InlineKeyboardMarkup([
    [t.InlineKeyboardButton("Official Grap W/H Groups", url="https://t.me/Dyna_community")],
    [t.InlineKeyboardButton("Official Grap W/H", url="https://t.me/Seizer_updates")],
    [t.InlineKeyboardButton("Community Groups", url="https://t.me/dynamic_gangs")]
])

# Fungsi untuk memeriksa keanggotaan pengguna
async def check_membership(user_id):
    is_member_group = False
    is_member_channel = False
    is_member_community = False

    valid_statuses = [
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER
    ]

    # Periksa keanggotaan di grup support
    try:
        member_group = await bot.get_chat_member(SUPPORT_CHAT_ID, user_id)
        is_member_group = member_group.status in valid_statuses
        print(f"User {user_id} - Group membership status: {member_group.status}")
    except UserNotParticipant:
        print(f"User {user_id} is not a participant in the group.")
    except Exception as e:
        print(f"Error checking group membership for user {user_id}: {e}")

    # Periksa keanggotaan di channel
    try:
        member_channel = await bot.get_chat_member(CHANNEL_ID, user_id)
        is_member_channel = member_channel.status in valid_statuses
        print(f"User {user_id} - Channel membership status: {member_channel.status}")
    except UserNotParticipant:
        print(f"User {user_id} is not a participant in the channel.")
    except Exception as e:
        print(f"Error checking channel membership for user {user_id}: {e}")

    # Periksa keanggotaan di grup community
    try:
        member_community = await bot.get_chat_member(COMMUNITY_GROUP_ID, user_id)
        is_member_community = member_community.status in valid_statuses
        print(f"User {user_id} - Community membership status: {member_community.status}")
    except UserNotParticipant:
        print(f"User {user_id} is not a participant in the community group.")
    except Exception as e:
        print(f"Error checking community membership for user {user_id}: {e}")

    print(f"User {user_id} - Group member: {is_member_group}, Channel member: {is_member_channel}, Community member: {is_member_community}")
    return is_member_group, is_member_channel, is_member_community

# Fungsi untuk mendapatkan karakter unik
async def get_unique_character(receiver_id, target_rarities=['🔵 Low', '🟢 Medium', '🔴 High', '🟡 Nobel', '🔮 Limited', '🥵 Nudes']):
    """
    Fetches a unique character for the user. If no unique character is found, fetches any random character.
    """
    try:
        # Fetch user's owned characters
        user_data = await user_collection.find_one({'id': receiver_id}, {'characters': 1})
        owned_character_ids = [char['id'] for char in user_data.get('characters', [])] if user_data else []

        # Attempt to fetch a unique character
        pipeline = [
            {'$match': {'rarity': {'$in': target_rarities}, 'id': {'$nin': owned_character_ids}}},
            {'$sample': {'size': 1}}
        ]
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=1)

        # If no unique character found, fetch any random character
        if not characters:
            random_character_pipeline = [{'$sample': {'size': 1}}]
            random_cursor = collection.aggregate(random_character_pipeline)
            characters = await random_cursor.to_list(length=1)

        return characters[0] if characters else None
    except Exception as e:
        print(f"Error fetching character: {e}")
        return None


@bot.on_message(filters.command(["claim"]))
async def claim_command(_, message: t.Message):
    user_id = message.from_user.id
    mention = message.from_user.mention

    # Check user's group/channel membership
    is_member_group, is_member_channel, is_member_community = await check_membership(user_id)
    if not is_member_group and not is_member_channel and not is_member_community:
        return await message.reply_text(
            "You must join the official groups, channels, and community group to use this command.",
            reply_markup=keyboard_all
        )
    elif not is_member_group:
        return await message.reply_text(
            "You must join the official group to use this command.",
            reply_markup=keyboard_support
        )
    elif not is_member_channel:
        return await message.reply_text(
            "You must join the official channel to use this command.",
            reply_markup=keyboard_channel
        )
    elif not is_member_community:
        return await message.reply_text(
            "You must join the community group to use this command.",
            reply_markup=keyboard_community
        )

    # Ensure user exists in the database
    user_data = await user_collection.find_one({'id': user_id})
    if not user_data:
        await user_collection.insert_one({'id': user_id, 'characters': [], 'last_claim_time': None})

    # Check if the user has already claimed today
    now = datetime.utcnow()
    last_claim_time = user_data.get('last_claim_time')
    if last_claim_time and last_claim_time.date() == now.date():
        return await message.reply_text("You have already claimed your character today. Come back tomorrow!")

    # Update last claim time
    await user_collection.update_one({'id': user_id}, {'$set': {'last_claim_time': now}})

    # Fetch a character
    character = await get_unique_character(user_id)

    # Ensure the character is added to the user's collection
    if character:
        await user_collection.update_one({'id': user_id}, {'$push': {'characters': character}})
        img_url = character['img_url']
        caption = (
            f"╭── ˹ ᴛᴏᴅᴀʏ'ꜱ ʀᴇᴡᴀʀᴅ ˼ ──•\n"
            f"┆\n"
            f"┊◍ 𝖮𝗐𝖮 {mention} won this character today! 💘\n"
            f"┆◍ ❄️ Name: {character['name']}\n"
            f"┊● ⚜️ Rarity: {character['rarity']}\n"
            f"┆● ⛩️ Anime: {character['anime']}\n"
            f"├──˹ ᴄᴏᴍᴇ ʙᴀᴄᴋ ᴛᴏᴍᴏʀʀᴏᴡ ˼──•\n"
            f"╰───────────────•\n"
        )
        return await message.reply_photo(photo=img_url, caption=caption)
    else:
        return await message.reply_text("An unexpected error occurred. Please try again later.")
