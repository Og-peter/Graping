import asyncio
from pyrogram import filters, Client, types as t
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shivu import shivuu as app, SPECIALGRADE
from shivu import shivuu as bot
from shivu import user_collection, collection
from datetime import datetime, timedelta
from pyrogram.errors import UserNotParticipant

# Constants
SUPPORT_CHAT_ID = -1002466950912  # Replace with your group chat ID
SUPPORT_URL = "https://t.me/Dyna_community"

# Inline Keyboards
join_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("🌌 Join Support Group 🌌", url=SUPPORT_URL)]
])

# Cooldown Dictionary
last_claim_time = {}

# Helper Functions
async def get_claim_state():
    """Get the current claim system state."""
    return "True"  # Claiming always enabled

async def add_claim_user(user_id):
    """Mark the user as having claimed a reward."""
    await user_collection.update_one({"id": user_id}, {"$set": {"claim": True}}, upsert=True)

async def get_unique_characters(rarities):
    """Fetch a unique character based on rarity."""
    try:
        pipeline = [
            {"$match": {"rarity": {"$in": rarities}}},
            {"$sample": {"size": 1}}
        ]
        cursor = collection.aggregate(pipeline)
        return await cursor.to_list(length=1)
    except Exception as e:
        print(f"Error fetching character: {e}")
        return []

# Command Handlers
@bot.on_message(filters.command("claim"))
async def claim_handler(_, message: t.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    mention = message.from_user.mention

    # Restrict to specific group
    if chat_id != SUPPORT_CHAT_ID:
        return await message.reply_text(
            f"🔒 **This command can only be used in the** [Support Group]({SUPPORT_URL}).",
            disable_web_page_preview=True
        )

    # Check group membership
    try:
        await bot.get_chat_member(SUPPORT_CHAT_ID, user_id)
    except UserNotParticipant:
        return await message.reply_text(
            "⚠️ **Join the group to claim your reward!**",
            reply_markup=join_keyboard
        )

    # Check channel subscription
    channel_username = "dynamic_supports"  # Replace with your channel username
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

    # Claiming always enabled
    claim_state = await get_claim_state()
    if claim_state == "False":
        return await message.reply_text("❌ **Claiming is currently disabled.**\n🕒 **Stay tuned for updates.**")

    # Cooldown Check
    now = datetime.now()
    if user_id in last_claim_time and last_claim_time[user_id].date() == now.date():
        next_claim = (last_claim_time[user_id] + timedelta(days=1)).strftime("%H:%M:%S")
        return await message.reply_text(
            f"🕒 **You've already claimed today!**\n⏳ **Next Claim Available:** `{next_claim}`"
        )

    # Claiming Animation
    animation = ["❄️", "🌸", "🌧️", "🐳", "🌟", "🎉"]
    temp_msg = await message.reply_text(animation[0])
    for icon in animation[1:]:
        await asyncio.sleep(0.8)
        await temp_msg.edit(icon)

    # Fetch character
    rarities = ['🔵 Low', '🟢 Medium', '🔴 High', '🟡 Nobel', '🔮 Limited', '🥵 Nudes']
    characters = await get_unique_characters(rarities)
    if not characters:
        return await temp_msg.edit("⚠️ **No characters available. Try again later!**")

    character = characters[0]
    img_url = character.get('img_url', '')
    char_name = character.get('name', 'Unknown')
    char_anime = character.get('anime', 'Unknown')
    char_rarity = character.get('rarity', '🔵 Low')

    # Save character and cooldown
    last_claim_time[user_id] = now
    await add_claim_user(user_id)
    await user_collection.update_one(
        {"id": user_id},
        {"$push": {"characters": character}},
        upsert=True
    )

    # Send Reward
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

@bot.on_message(filters.command("resetclaim") & filters.user(SPECIALGRADE))
async def reset_claim(_, message: t.Message):
    global last_claim_time
    last_claim_time.clear()
    await user_collection.update_many({}, {"$unset": {"claim": ""}})
    await message.reply_text(
        "🔄 **All cooldowns have been reset!**\n🎯 **Users can now claim again without waiting.**"
    )
