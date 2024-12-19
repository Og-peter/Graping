import asyncio
from pyrogram import filters, Client, types as t
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shivu import shivuu as bot, DEV_LIST
from shivu import user_collection, collection
from datetime import datetime, timedelta
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant

# Constants
SUPPORT_CHAT_ID = -1002466950912  # Replace with your group chat ID
SUPPORT_URL = "https://t.me/Dyna_community"

# Advanced Keyboard
join_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("🌌 Join Support Group 🌌", url=SUPPORT_URL)]
])

# Cooldown Dictionary
last_claim_time = {}

# Helper Functions
async def claim_toggle(state):
    """Toggle the claim state between enabled/disabled."""
    await collection.update_one({}, {"$set": {"claim": state}}, upsert=True)

async def get_claim_state():
    """Fetch the claim system's current state."""
    doc = await collection.find_one({})
    return doc.get("claim", "False")

async def add_claim_user(user_id):
    """Mark the user as claimed."""
    await user_collection.update_one({"id": user_id}, {"$set": {"claim": True}}, upsert=True)

async def get_unique_characters(receiver_id, rarities=['🔵 Low', '🟢 Medium', '🔴 High', '🟡 Nobel', '🔮 Limited', '🥵 Nudes']):
    """Get a unique character for the claiming process."""
    try:
        pipeline = [
            {'$match': {'rarity': {'$in': rarities}}},
            {'$sample': {'size': 1}}  # Get a random character
        ]
        cursor = collection.aggregate(pipeline)
        return await cursor.to_list(length=1)
    except Exception as e:
        print(f"Error in fetching character: {e}")
        return []

# Command Handlers
@bot.on_message(filters.command("startclaim") & filters.user(DEV_LIST))
async def start_claim(_, message: t.Message):
    await claim_toggle("True")
    await message.reply_text(
        "✨ **Claiming Feature Activated!**\n\n"
        "🌟 **Users can now start claiming their favorite characters.**\n"
        "🔔 **Don't forget to check the group for more events!**"
    )

@bot.on_message(filters.command("stopclaim") & filters.user(DEV_LIST))
async def stop_claim(_, message: t.Message):
    await claim_toggle("False")
    await message.reply_text(
        "🚫 **Claiming Feature Disabled!**\n\n"
        "❌ **Users cannot claim rewards for now. Stay tuned for updates!**"
    )

@bot.on_message(filters.command("claim"))
async def claim_handler(_, message: t.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    mention = message.from_user.mention

    # Group Restriction
    if chat_id != SUPPORT_CHAT_ID:
        return await message.reply_text(
            f"🔒 **This command can only be used in the** [Support Group]({SUPPORT_URL}).",
            disable_web_page_preview=True
        )

    # Join Group Check
    try:
        await bot.get_chat_member(SUPPORT_CHAT_ID, user_id)
    except UserNotParticipant:
        return await message.reply_text(
            "⚠️ **Join the group to claim your reward!**",
            reply_markup=join_keyboard
        )

    # Channel Subscription Check
    channel_username = "dynamic_supports"  # Replace with your channel's username
    try:
        await bot.get_chat_member(channel_username, user_id)
    except UserNotParticipant:
        return await message.reply_text(
            "📢 **Subscribe to the channel to claim rewards!**\n\n"
            f"🔗 **Join here:** [Support Channel](https://t.me/{channel_username})",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔔 Join Support Channel 🔔", url=f"https://t.me/{channel_username}")]
            ])
        )

    # Claim System Check
    claim_state = await get_claim_state()
    if claim_state == "False":
        return await message.reply_text(
            "❌ **Claiming is currently disabled.**\n"
            "🕒 **Stay tuned for updates.**"
        )

    # Cooldown Check
    now = datetime.now()
    if user_id in last_claim_time:
        last_claim_date = last_claim_time[user_id]
        if last_claim_date.date() == now.date():
            next_claim = (last_claim_date + timedelta(days=1)).strftime("%H:%M:%S")
            return await message.reply_text(
                f"🕒 **You've already claimed today!**\n"
                f"⏳ **Next Claim Available:** `{next_claim}`"
            )

    # Claim Animation
    claiming_messages = [
        "❄️",
        "🌸",
        "🌧️",
        "🐋"
    ]
    temp_msg = await message.reply_text(claiming_messages[0])
    for msg in claiming_messages[1:]:
        await asyncio.sleep(1.5)
        await temp_msg.edit(msg)

    # Fetch Character
    characters = await get_unique_characters(user_id)
    if not characters:
        return await temp_msg.edit("⚠️ **No characters available. Try again later!**")

    # Save and Send Character
    character = characters[0]
    img_url = character.get('img_url', '')
    char_name = character.get('name', 'Unknown')
    char_anime = character.get('anime', 'Unknown')
    char_rarity = character.get('rarity', '🔵 Low')

    last_claim_time[user_id] = now
    await add_claim_user(user_id)
    await user_collection.update_one(
        {"id": user_id},
        {"$push": {"characters": character}}
    )

    # Reward Message
    reward_message = f"""
🎉 **Congrats, {mention}!**

✨ **Character Claimed:**
- **🍁 Name:** `{char_name}`
- **⛩️ Anime:** `{char_anime}`
- **🪷 Rarity:** `{char_rarity}`

🔔 **Claim another reward tomorrow!**
"""
    await temp_msg.delete()
    await message.reply_photo(photo=img_url, caption=reward_message)

# Reset Cooldown Command
@bot.on_message(filters.command("resetclaim") & filters.user(DEV_LIST))
async def reset_claim(_, message: t.Message):
    """Reset claim cooldown for all users."""
    global last_claim_time
    last_claim_time.clear()
    await user_collection.update_many({}, {"$unset": {"claim": ""}})
    await message.reply_text(
        "🔄 **All cooldowns have been reset!**\n"
        "🎯 **Users can now claim again without waiting.**"
    )
