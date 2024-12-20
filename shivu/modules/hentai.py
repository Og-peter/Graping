import asyncio
import random
import time
from pyrogram import filters, Client, types as t
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shivu import shivuu as bot
from shivu import collection, user_collection

# Cooldown, usage limits, and temporary storage
user_sessions = {}  # Tracks active user sessions
cooldowns = {}
daily_usage = {}  # Tracks daily usage for /find and /hfind commands
DAILY_LIMIT = 20  # Limit per day
EXTRA_BALANCE_COST = 50  # Cost to extend usage after limit

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

async def update_usage(user_id, command):
    """Update the usage count for the user and check if the limit is exceeded."""
    if user_id not in daily_usage:
        daily_usage[user_id] = {'find': 0, 'hfind': 0}

    daily_usage[user_id][command] += 1
    if daily_usage[user_id][command] > DAILY_LIMIT:
        return True  # Limit exceeded
    return False

async def deduct_balance(user_id, amount):
    """Deduct balance from the user's account."""
    user_data = await user_collection.find_one({'id': user_id})
    if not user_data or user_data.get('balance', 0) < amount:
        return False  # Insufficient balance

    await user_collection.update_one({'id': user_id}, {'$inc': {'balance': -amount}})
    return True

@bot.on_message(filters.command(["find"]))
async def find_character(_, message: t.Message):
    """Discover a random character."""
    user_id = message.from_user.id
    mention = message.from_user.mention

    # Cooldown check
    if user_id in cooldowns and time.time() - cooldowns[user_id] < 30:
        cooldown_time = int(30 - (time.time() - cooldowns[user_id]))
        return await message.reply_text(f"⏳ Horny? Wait {cooldown_time} seconds to start a new round with a new character 🌚.", quote=True)

    # Update cooldown
    cooldowns[user_id] = time.time()

    # Check daily usage
    if user_id not in daily_usage:
        daily_usage[user_id] = {'find': 0}

    if daily_usage[user_id]['find'] < 5:
        # Free usage
        daily_usage[user_id]['find'] += 1
    else:
        # After free limit, deduct balance
        entry_fee = 1000
        user_data = await user_collection.find_one({'id': user_id})
        user_balance = user_data.get('balance', 0) if user_data else 0

        if user_balance < entry_fee:
            return await message.reply_text(
                f"❌ You have exhausted your 5 free daily `/find` uses.\n"
                f"Your current balance is ₩{user_balance}, but you need ₩{entry_fee} to continue.\n"
                f"Please recharge your balance or wait for the next day to get 5 free tries!",
                quote=True
            )

        # Deduct entry fee from balance
        await user_collection.update_one({'id': user_id}, {'$inc': {'balance': -entry_fee}})
        daily_usage[user_id]['find'] += 1

    # Fetch a random character
    character = await fetch_character()
    if not character:
        return await message.reply_text("❌ Character not found because your dick size is too small. Please try again later.", quote=True)

    # Check if character is already in session
    if user_sessions.get(user_id) == character['id']:
        return await message.reply_text(
            f"❌ {mention}, you're already on the bed with {character['name']}! 🛏️\n"
            f"First finish your job with them, then try another one. 😏",
            quote=True
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
            f"🌚 {mention}, a random character is ready on your bed 🌚🌚\n\n"
            f"❄️ **Name**: {character['name']}\n"
            f"🏮 **Rarity**: {character['rarity']}\n"
            f"⛩️ **Anime**: {character['anime']}\n"
            f"👀 **Age**: <b><font color='pink'>{random.randint(18, 40)}</font></b> (Just the right age 😉)\n\n"
            f"⚔️ Ready to fight on the bed? Choose to **fight** or **ignore**!\n\n"
            f"Use the buttons below to make your move! 🗿"
        ),
        reply_markup=keyboard,
    )

@bot.on_message(filters.command(["hfind"]))
async def hfind_character(_, message: t.Message):
    """Search and fight a specific character by ID."""
    user_id = message.from_user.id
    mention = message.from_user.mention

    if len(message.command) < 2:
        return await message.reply_text("Please specify the character ID, e.g., `/hfind 1234`.", quote=True)

    character_id = message.command[1]

    # Check daily limit
    if await update_usage(user_id, 'hfind'):
        # Deduct balance if user wants to break the limit
        if not await deduct_balance(user_id, EXTRA_BALANCE_COST):
            return await message.reply_text(
                f"❌ You've reached your daily limit of {DAILY_LIMIT} `/hfind` uses.\n"
                f"Spend ₩{EXTRA_BALANCE_COST} to extend your limit or try again tomorrow.",
                quote=True
            )

    # Fetch the character by ID
    character = await fetch_character(query=character_id)
    if not character:
        return await message.reply_text(f"No character found with ID `{character_id}`. Please try another.", quote=True)

    # Check if character is already in session
    if user_sessions.get(user_id) == character['id']:
        return await message.reply_text(
            f"❌ {mention}, you're already on the bed with {character['name']}! 🛏️\n"
            f"First finish your job with them, then try another one. 😏",
            quote=True
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
            f"🌚 {mention}, a random character is ready on your bed 🌚🌚\n\n"
            f"❄️ **Name**: {character['name']}\n"
            f"🏮 **Rarity**: {character['rarity']}\n"
            f"⛩️ **Anime**: {character['anime']}\n"
            f"👀 **Age**: <b><font color='pink'>{random.randint(18, 40)}</font></b> (Just the right age 😉)\n\n"
            f"⚔️ Ready to fight on the bed? Choose to **fight** or **ignore**!\n\n"
            f"Use the buttons below to make your move! 🗿"
    ),
        reply_markup=keyboard,
    )

@bot.on_callback_query(filters.regex(r"^(fight|ignore)_(\d+)$"))
async def fight_or_ignore_callback(_, callback_query: t.CallbackQuery):
    """Handle fight or ignore options."""
    action, user_id = callback_query.data.split("_")
    user_id = int(user_id)
    mention = callback_query.from_user.mention

    # Ensure the callback is for the correct user
    if callback_query.from_user.id != user_id:
        return await callback_query.answer("This is not your interaction!", show_alert=True)

    # Fetch character data from session
    character = await fetch_character(user_sessions.get(user_id))
    if not character:
        return await callback_query.answer("Character data not found. Please use /find or /hfind again.", show_alert=True)

    if action == "ignore":
        await callback_query.message.edit_text(f"❌ {mention}, you ignored {character['name']}.\nTry searching again with `/find` or `/hfind`!")
        user_sessions.pop(user_id, None)
    elif action == "fight":
        await callback_query.answer("⚔️ Fight initiated!", show_alert=True)
        await handle_fight(callback_query, user_id, character)

async def handle_fight(callback_query, user_id, character):
    """Handle fight simulation."""
    mention = callback_query.from_user.mention

    # Random outcome for fight
    user_wins = random.choice([True, False])

    if user_wins:
        result_text = f"🎉 {mention}, you won the bed fight against {character['name']}!\nThe character is now yours!"
        await user_collection.update_one({'id': user_id}, {'$push': {'characters': character}})
    else:
        result_text = (
            f"💔 {mention}, you lost the fight against {character['name']}.\n"
            f"😔 Seems like your dick is not useful on the bed. Better luck next time!"
        )

    await callback_query.message.edit_text(result_text)

    # Clear session
    user_sessions.pop(user_id, None)
