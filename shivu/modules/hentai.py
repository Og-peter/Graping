import asyncio
import random
import time
from pyrogram import filters, Client, types as t
from itertools import groupby
from html import escape
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
            [InlineKeyboardButton("🌚 Semx ", callback_data=f"fight_{user_id}")],
            [InlineKeyboardButton("❌ Ignore (black) 🌝", callback_data=f"ignore_{user_id}")]
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
            f"⚔️ Ready to semx fight on the bed? Choose to **semx** or **ignore**!\n\n"
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

    # Cooldown check
    if user_id in cooldowns and time.time() - cooldowns[user_id] < 30:
        cooldown_time = int(30 - (time.time() - cooldowns[user_id]))
        return await message.reply_text(f"⏳ Horny? Wait {cooldown_time} seconds to start a new round with a new character 🌚.", quote=True)

    # Update cooldown
    cooldowns[user_id] = time.time()

    # Check daily usage
    if user_id not in daily_usage:
        daily_usage[user_id] = {'hfind': 0}

    if daily_usage[user_id]['hfind'] < 5:
        # Free usage
        daily_usage[user_id]['hfind'] += 1
    else:
        # After free limit, deduct balance
        entry_fee = 2000
        user_data = await user_collection.find_one({'id': user_id})
        user_balance = user_data.get('balance', 0) if user_data else 0

        if user_balance < entry_fee:
            return await message.reply_text(
                f"❌ You have exhausted your 5 free daily `/hfind` uses.\n"
                f"Your current balance is ₩{user_balance}, but you need ₩{entry_fee} to continue.\n"
                f"Please recharge your balance or wait for the next day to get 5 free tries!",
                quote=True
            )

        # Deduct entry fee from balance
        await user_collection.update_one({'id': user_id}, {'$inc': {'balance': -entry_fee}})
        daily_usage[user_id]['hfind'] += 1

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
            [InlineKeyboardButton("🌚 Semx", callback_data=f"fight_{user_id}")],
            [InlineKeyboardButton("❌ Ignore (black 🌝)", callback_data=f"ignore_{user_id}")]
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
            f"⚔️ Ready to semx fight on the bed? Choose to **semx** or **ignore**!\n\n"
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
        result_text = f"🎉 {mention}, you won the bed semx fight against {character['name']}!\nThe character is now yours!"
        await user_collection.update_one({'id': user_id}, {'$push': {'characters': character}})
    else:
        result_text = (
            f"💔 {mention}, you lost the fight against {character['name']}.\n"
            f"😔 Seems like your dick is not useful on the bed. Better luck next time!"
        )

    await callback_query.message.edit_text(result_text)

    # Clear session
    user_sessions.pop(user_id, None)
    
@bot.on_message(filters.command(["collection"]))
async def paginated_collection(_, message: t.Message):
    """Display the user's collection with pagination."""
    user_id = message.from_user.id
    mention = message.from_user.mention

    # Fetch user data
    user_data = await user_collection.find_one({'id': user_id})
    if not user_data or 'characters' not in user_data or len(user_data['characters']) == 0:
        return await message.reply_text(
            f"❌ {mention}, your collection is empty.\nStart collecting characters using `/find` or `/hfind`!",
            quote=True
        )

    # Pagination setup
    page = 0  # Default to page 1
    characters = sorted(user_data['characters'], key=lambda x: x['anime'])  # Group by anime
    total_pages = (len(characters) + 9) // 10  # 10 characters per page

    # Character count by ID for duplicate characters
    character_counts = {}
    for char in characters:
        character_counts[char['id']] = character_counts.get(char['id'], 0) + 1

    # Generate harem message
    harem_message = f"<b>{escape(message.from_user.first_name)}'s ʜᴀʀᴇᴍ - ᴘᴀɢᴇ {page + 1}/{total_pages}</b>\n"

    # Group characters by anime
    current_characters = characters[page * 10:(page + 1) * 10]
    current_grouped_characters = {k: list(v) for k, v in groupby(current_characters, key=lambda x: x['anime'])}
    included_characters = set()

    for anime, characters in current_grouped_characters.items():
        user_anime_count = len([char for char in user_data['characters'] if isinstance(char, dict) and char.get('anime') == anime])
        total_anime_count = await collection.count_documents({"anime": anime})

        harem_message += f'\n⌬ <b>{anime} 〔{user_anime_count}/{total_anime_count}〕</b>\n'
        harem_message += f'⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋\n'

        for character in characters:
            if character['id'] not in included_characters:
                count = character_counts[character['id']]
                formatted_id = f"{int(character['id']):04d}"
                harem_message += f'➥ {formatted_id} | {character["rarity"][0]} | {character["name"]} ×{count}\n'
                included_characters.add(character['id'])
        harem_message += f'⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋\n'

    # Inline buttons for navigation and viewing individual characters
    keyboard = [
        [
            InlineKeyboardButton("⏪ Previous", callback_data=f"collection_page_{user_id}_{page - 1}"),
            InlineKeyboardButton("Next ⏩", callback_data=f"collection_page_{user_id}_{page + 1}")
        ],
        [InlineKeyboardButton("sᴇᴇ ʜᴀʀᴇᴍ", switch_inline_query_current_chat=f"collection.{user_id}")]
    ]

    # Send the paginated collection
    await message.reply_text(
        harem_message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )

@bot.on_callback_query(filters.regex(r"collection_page_(\d+)_(\d+)"))
async def paginate_collection(_, callback_query: t.CallbackQuery):
    """Handle pagination for the user's collection."""
    user_id, page = map(int, callback_query.data.split("_")[1:])
    user_data = await user_collection.find_one({'id': user_id})
    if not user_data or 'characters' not in user_data or len(user_data['characters']) == 0:
        return await callback_query.answer("No characters in the collection.", show_alert=True)

    # Ensure valid page
    characters = sorted(user_data['characters'], key=lambda x: x['anime'])
    total_pages = (len(characters) + 9) // 10
    if page < 0 or page >= total_pages:
        return await callback_query.answer("Invalid page.", show_alert=True)

    # Character count by ID for duplicates
    character_counts = {}
    for char in characters:
        character_counts[char['id']] = character_counts.get(char['id'], 0) + 1

    # Generate harem message for the current page
    harem_message = f"<b>{escape(callback_query.from_user.first_name)}'s ʜᴀʀᴇᴍ - ᴘᴀɢᴇ {page + 1}/{total_pages}</b>\n"

    current_characters = characters[page * 10:(page + 1) * 10]
    current_grouped_characters = {k: list(v) for k, v in groupby(current_characters, key=lambda x: x['anime'])}
    included_characters = set()

    for anime, characters in current_grouped_characters.items():
        user_anime_count = len([char for char in user_data['characters'] if isinstance(char, dict) and char.get('anime') == anime])
        total_anime_count = await collection.count_documents({"anime": anime})

        harem_message += f'\n⌬ <b>{anime} 〔{user_anime_count}/{total_anime_count}〕</b>\n'
        harem_message += f'⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋\n'

        for character in characters:
            if character['id'] not in included_characters:
                count = character_counts[character['id']]
                formatted_id = f"{int(character['id']):04d}"
                harem_message += f'➥ {formatted_id} | {character["rarity"][0]} | {character["name"]} ×{count}\n'
                included_characters.add(character['id'])
        harem_message += f'⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋\n'

    # Inline buttons for navigation
    keyboard = [
        [
            InlineKeyboardButton("⏪ Previous", callback_data=f"collection_page_{user_id}_{page - 1}"),
            InlineKeyboardButton("Next ⏩", callback_data=f"collection_page_{user_id}_{page + 1}")
        ],
        [InlineKeyboardButton("sᴇᴇ ʜᴀʀᴇᴍ", switch_inline_query_current_chat=f"collection.{user_id}")]
    ]

    # Edit the original message with updated content
    await callback_query.message.edit_text(
        harem_message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )
