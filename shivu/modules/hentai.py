import asyncio
import random
import time
from pyrogram import filters, Client, types as t
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shivu import shivuu as bot
from shivu import collection, user_collection

# Cooldown and temporary storage
user_sessions = {}  # Tracks active user sessions
cooldowns = {}

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

    # Fetch a random character
    character = await fetch_character()
    if not character:
        return await message.reply_text("❌ Character not found because your dick size is too small. Please try again later.", quote=True)

    # Check if character is already in session or defeated
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
            [InlineKeyboardButton("⚔️ semx", callback_data=f"fight_{user_id}")],
            [InlineKeyboardButton("❌ Ignore (black 🌚)", callback_data=f"ignore_{user_id}")]
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
            f"⚔️ Ready to semx on the bed? Choose to **semx** or **ignore**!\n\n"
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

    # Fetch the character by ID
    character = await fetch_character(query=character_id)
    if not character:
        return await message.reply_text(f"No character found with ID `{character_id}`. Please try another.", quote=True)

    # Check if character is already in session or defeated
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
            [InlineKeyboardButton("⚔️ Semx", callback_data=f"fight_{user_id}")],
            [InlineKeyboardButton("❌ Ignore (black 🌚)", callback_data=f"ignore_{user_id}")]
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
            f"⚔️ Ready to semx on the bed? Choose to **semx** or **ignore**!\n\n"
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
        await callback_query.answer("⚔️ Semx initiated!", show_alert=True)
        await handle_fight(callback_query, user_id, character)

async def handle_fight(callback_query, user_id, character):
    """Handle fight simulation."""
    mention = callback_query.from_user.mention

    # Random outcome for fight
    user_wins = random.choice([True, False])

    if user_wins:
        result_text = f"🎉 {mention}, you won the bed semx fight 🌚 against {character['name']}!\nThe character is now yours!"
        await user_collection.update_one({'id': user_id}, {'$push': {'characters': character}})
    else:
        result_text = (
            f"💔 {mention}, you lost the against {character['name']}.\n"
            f"😔 Seems like your dick is not useful on the bed. Better luck next time!"
        )

    await callback_query.message.edit_text(result_text)

    # Clear session
    user_sessions.pop(user_id, None)
