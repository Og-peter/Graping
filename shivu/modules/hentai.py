import asyncio
import random
import time
from datetime import datetime
from pyrogram import filters, Client, types as t
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shivu import shivuu as bot
from shivu import collection, user_collection

# Cooldown, temporary storage, and daily usage tracking
user_sessions = {}
cooldowns = {}
daily_usage = {}  # Tracks daily usage for commands
limits_removed = {}  # Tracks users who paid to remove limits

# Command-specific limits and fees
LIMITS = {
    "find": {"daily_limit": 20, "fee": 50, "limit_removal_fee": 2000},
    "hfind": {"daily_limit": 10, "fee": 100, "limit_removal_fee": 2000},
}

async def fetch_character(query=None):
    """Fetch a character randomly or by specific query (ID)."""
    try:
        if query:
            character = await collection.find_one({'id': query})
        else:
            pipeline = [{'$sample': {'size': 1}}]
            cursor = collection.aggregate(pipeline)
            character = await cursor.to_list(length=1)
            character = character[0] if character else None
        return character
    except Exception as e:
        print(e)
        return None

async def update_daily_usage(user_id, command):
    """Update daily usage and reset if needed."""
    today = datetime.now().strftime('%Y-%m-%d')
    if user_id not in daily_usage or daily_usage[user_id]['date'] != today:
        daily_usage[user_id] = {'date': today, 'counts': {"find": 0, "hfind": 0}}
    daily_usage[user_id]['counts'][command] += 1

async def check_limit_and_fee(user_id, command):
    """Check if user exceeded the daily limit and handle fee deduction."""
    today = datetime.now().strftime('%Y-%m-%d')
    if user_id not in daily_usage or daily_usage[user_id]['date'] != today:
        daily_usage[user_id] = {'date': today, 'counts': {"find": 0, "hfind": 0}}

    # Check if the limit has been removed for the user
    if limits_removed.get(user_id, {}).get(command, False):
        return True, 0

    # Check daily usage
    if daily_usage[user_id]['counts'][command] < LIMITS[command]["daily_limit"]:
        return True, 0

    return False, LIMITS[command]["limit_removal_fee"]

@bot.on_message(filters.command(["find", "hfind"]))
async def find_or_hfind_character(_, message: t.Message):
    """Handle /find and /hfind commands separately."""
    command = message.command[0].lower()
    user_id = message.from_user.id
    mention = message.from_user.mention

    # Handle daily limit and fee
    allowed, removal_fee = await check_limit_and_fee(user_id, command)
    if not allowed:
        # Offer to remove the limit with buttons
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("✅ Accept", callback_data=f"remove_limit_{command}_{user_id}")],
                [InlineKeyboardButton("❌ Decline", callback_data="decline_limit")]
            ]
        )
        return await message.reply_text(
            f"❌ {mention}, you've reached your daily limit of {LIMITS[command]['daily_limit']} free attempts for `{command}`.\n"
            f"To remove the limit, it will cost ₩{removal_fee}. Would you like to proceed?",
            reply_markup=keyboard,
            quote=True,
        )

    # Cooldown check
    if user_id in cooldowns and time.time() - cooldowns[user_id] < 30:
        cooldown_time = int(30 - (time.time() - cooldowns[user_id]))
        return await message.reply_text(f"⏳ Please wait {cooldown_time} seconds before trying again.", quote=True)
    cooldowns[user_id] = time.time()

    # Update daily usage
    await update_daily_usage(user_id, command)

    # Fetch character
    character_id = message.command[1] if command == "hfind" and len(message.command) > 1 else None
    character = await fetch_character(query=character_id if command == "hfind" else None)
    if not character:
        return await message.reply_text("❌ Character not found. Please try again later.", quote=True)

    # Check if character is already in session
    if user_sessions.get(user_id) == character['id']:
        return await message.reply_text(
            f"❌ {mention}, you're already interacting with {character['name']}! Finish this session before starting a new one.",
            quote=True,
        )

    # Save session
    user_sessions[user_id] = character['id']

    # Display character with options
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⚔️ Fight", callback_data=f"fight_{user_id}")],
            [InlineKeyboardButton("❌ Ignore", callback_data=f"ignore_{user_id}")]
        ]
    )
    await message.reply_photo(
        photo=character['img_url'],
        caption=(
            f"🌚 {mention}, a character is ready for you 🌚🌚\n\n"
            f"❄️ **Name**: {character['name']}\n"
            f"🏮 **Rarity**: {character['rarity']}\n"
            f"⛩️ **Anime**: {character['anime']}\n"
            f"👀 **Age**: {random.randint(18, 40)} (Just the right age 😉)\n\n"
            f"⚔️ Ready to fight? Choose to **fight** or **ignore**!"
        ),
        reply_markup=keyboard,
    )

@bot.on_callback_query(filters.regex(r"remove_limit_(find|hfind)_(\d+)"))
async def remove_limit_callback(_, callback_query: t.CallbackQuery):
    """Handle removing the daily limit via buttons."""
    command, user_id = callback_query.data.split("_")[1:]
    user_id = int(user_id)

    # Ensure the correct user interacts
    if callback_query.from_user.id != user_id:
        return await callback_query.answer("This is not your interaction!", show_alert=True)

    user_data = await user_collection.find_one({'id': user_id})
    balance = user_data.get('balance', 0) if user_data else 0
    fee = LIMITS[command]["limit_removal_fee"]

    if balance < fee:
        return await callback_query.answer(
            f"❌ You don't have enough balance (₩{fee}). Earn more and try again.",
            show_alert=True,
        )

    # Deduct fee and remove limit
    await user_collection.update_one({'id': user_id}, {'$inc': {'balance': -fee}})
    if user_id not in limits_removed:
        limits_removed[user_id] = {}
    limits_removed[user_id][command] = True

    await callback_query.edit_message_text(
        f"✅ You have successfully removed the daily limit for `{command}`! Enjoy unlimited usage."
    )

@bot.on_callback_query(filters.regex(r"decline_limit"))
async def decline_limit_callback(_, callback_query: t.CallbackQuery):
    """Handle the decline button for limit removal."""
    await callback_query.edit_message_text("❌ Limit removal canceled. Come back when you're ready!")

@bot.on_callback_query(filters.regex(r"(fight|ignore)_(\d+)"))
async def fight_or_ignore_callback(_, callback_query: t.CallbackQuery):
    """Handle fight or ignore interactions."""
    action, user_id = callback_query.data.split("_")
    user_id = int(user_id)

    # Ensure the correct user interacts
    if callback_query.from_user.id != user_id:
        return await callback_query.answer("This is not your interaction!", show_alert=True)

    if action == "fight":
        await callback_query.edit_message_text("⚔️ Fight initiated! Show your power!")
    elif action == "ignore":
        await callback_query.edit_message_text("❌ Ignored! Better luck next time.")
