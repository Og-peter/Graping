import asyncio
import random
import time
from pyrogram import filters, Client, types as t
from shivu import shivuu as bot
from shivu import user_collection, collection

# Configuration
win_rate_percentage = 40  # Probability of winning
cooldown_duration = 600  # Cooldown time in seconds
battle_fee = 0  # Fee for initiating a battle

user_cooldowns = {}  # Track user cooldowns

# Banned User IDs
ban_user_ids = {1234567890}

# Anime Arc Data
anime_arcs = [
    {
        "arc": "Naruto - Pain's Assault",
        "heroes": ["Naruto Uzumaki", "Kakashi Hatake"],
        "villains": ["Pain", "Konan"],
        "image": "https://files.catbox.moe/83rsnb.jpg",
    },
    {
        "arc": "One Piece - Marineford War",
        "heroes": ["Monkey D. Luffy", "Whitebeard"],
        "villains": ["Akainu", "Blackbeard"],
        "image": "https://files.catbox.moe/urb2aa.jpg",
    },
    {
        "arc": "Dragon Ball - Cell Saga",
        "heroes": ["Goku", "Gohan"],
        "villains": ["Cell", "Android 17"],
        "image": "https://files.catbox.moe/9arc3h.jpg",
    },
    {
        "arc": "Bleach - Hueco Mundo",
        "heroes": ["Ichigo Kurosaki", "Rukia Kuchiki"],
        "villains": ["Ulquiorra", "Grimmjow"],
        "image": "https://files.catbox.moe/v6q5a1.jpg",
    },
    {
        "arc": "Attack on Titan - Shiganshina",
        "heroes": ["Eren Yeager", "Mikasa Ackerman"],
        "villains": ["Zeke Yeager", "Reiner Braun"],
        "image": "https://files.catbox.moe/b814or.jpg",
    },
]

# List of rarities
rarities = ['🔵 Low', '🟢 Medium', '🔴 High', '🟡 Nobel', '🔮 Limited']  # Example rarities

# Helper Function: Human-readable cooldown
def human_readable_time(seconds: int) -> str:
    mins, secs = divmod(seconds, 60)
    return f"{mins}m {secs}s" if mins else f"{secs}s"

@bot.on_message(filters.command(["animearc"]))
async def anime_arc_battle(_, message: t.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    mention = message.from_user.mention

    # Check if the user is banned
    if user_id in ban_user_ids:
        return await message.reply_text("You are banned from using this command. Contact support for help.")

    # Check cooldown
    if user_id in user_cooldowns and time.time() - user_cooldowns[user_id] < cooldown_duration:
        remaining_time = cooldown_duration - int(time.time() - user_cooldowns[user_id])
        return await message.reply_text(f"Wait {human_readable_time(remaining_time)} before starting another battle!")

    # Fetch user balance from the database
    user_data = await user_collection.find_one({"id": user_id}, projection={"balance": 1})
    if not user_data:
        return await message.reply_text("User data not found. Please register first!")

    user_balance = user_data.get("balance", 0)
    if user_balance < battle_fee:
        return await message.reply_text("Insufficient tokens! You need 200000 tokens to start the battle.")

    # Deduct the battle fee
    await user_collection.update_one({"id": user_id}, {"$inc": {"balance": -battle_fee}})

    # Select a random anime arc
    selected_arc = random.choice(anime_arcs)

    # Set user cooldown
    user_cooldowns[user_id] = time.time()

    try:
        # Initial message with arc details
        start_message = (
            f"⚔️ **Anime Arc Battle** ⚔️\n\n**Arc:** {selected_arc['arc']}\n"
            f"**Heroes:** {', '.join(selected_arc['heroes'])}\n"
            f"**Villains:** {', '.join(selected_arc['villains'])}\n\n**Let the battle begin!**"
        )
        await bot.send_photo(chat_id, photo=selected_arc['image'], caption=start_message)

        # Simulate battle
        await asyncio.sleep(3)
        await message.reply_text("🌀 Heroes and Villains are fighting...")
        await asyncio.sleep(3)

        if random.random() < (win_rate_percentage / 100):
            # User wins, assign a random rarity and hero
            selected_rarity = random.choice(rarities)
            reward_character = random.choice(selected_arc['heroes'])
            reward_data = {
                "name": reward_character,
                "anime": selected_arc['arc'],
                "rarity": selected_rarity,
                "img_url": selected_arc['image'],
            }
            await user_collection.update_one(
                {"id": user_id}, {"$push": {"characters": reward_data}}
            )

            victory_message = (
                f"🎉 **Victory!**\n\n{mention}, you defeated the villains in **{selected_arc['arc']}**!\n"
                f"You earned a new hero: **{reward_character}**!\n**Rarity:** {selected_rarity}"
            )
            await bot.send_photo(chat_id, photo=selected_arc['image'], caption=victory_message)
        else:
            # User loses
            await message.reply_text(
                f"💀 {mention}, the villains overpowered you in **{selected_arc['arc']}**. Better luck next time!"
            )
    except Exception as e:
        print(f"Error: {e}")
        await message.reply_text("An error occurred. Please try again later.")
