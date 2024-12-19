import asyncio
import random
import time
from pyrogram import filters, Client, types as t
from shivu import shivuu as bot
from shivu import user_collection, collection

# Configuration
win_rate_percentage = 40  # Probability of winning
cooldown_duration = 600  # Cooldown time in seconds

user_cooldowns = {}  # Track user cooldowns

# Banned User IDs
ban_user_ids = {1234567890}

# Anime Arc Data with Individual Character Images
anime_arcs = [
    {
        "arc": "Naruto - Pain's Assault",
        "heroes": [
            {"name": "Naruto Uzumaki", "img_url": "https://files.catbox.moe/naruto.jpg"},
            {"name": "Kakashi Hatake", "img_url": "https://files.catbox.moe/kakashi.jpg"},
        ],
        "villains": ["Pain", "Konan"],
        "image": "https://files.catbox.moe/83rsnb.jpg",
    },
    {
        "arc": "One Piece - Marineford War",
        "heroes": [
            {"name": "Monkey D. Luffy", "img_url": "https://files.catbox.moe/luffy.jpg"},
            {"name": "Whitebeard", "img_url": "https://files.catbox.moe/whitebeard.jpg"},
        ],
        "villains": ["Akainu", "Blackbeard"],
        "image": "https://files.catbox.moe/urb2aa.jpg",
    },
    {
        "arc": "Dragon Ball - Cell Saga",
        "heroes": [
            {"name": "Goku", "img_url": "https://files.catbox.moe/goku.jpg"},
            {"name": "Gohan", "img_url": "https://files.catbox.moe/gohan.jpg"},
        ],
        "villains": ["Cell", "Android 17"],
        "image": "https://files.catbox.moe/9arc3h.jpg",
    },
    {
        "arc": "Bleach - Hueco Mundo",
        "heroes": [
            {"name": "Ichigo Kurosaki", "img_url": "https://files.catbox.moe/ichigo.jpg"},
            {"name": "Rukia Kuchiki", "img_url": "https://files.catbox.moe/rukia.jpg"},
        ],
        "villains": ["Ulquiorra", "Grimmjow"],
        "image": "https://files.catbox.moe/v6q5a1.jpg",
    },
    {
        "arc": "Attack on Titan - Shiganshina",
        "heroes": [
            {"name": "Eren Yeager", "img_url": "https://files.catbox.moe/eren.jpg"},
            {"name": "Mikasa Ackerman", "img_url": "https://files.catbox.moe/mikasa.jpg"},
        ],
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
        return await message.reply_text("🚫 You are banned from using this command. Contact support for help.")

    # Check cooldown
    if user_id in user_cooldowns and time.time() - user_cooldowns[user_id] < cooldown_duration:
        remaining_time = cooldown_duration - int(time.time() - user_cooldowns[user_id])
        return await message.reply_text(f"⏳ Wait {human_readable_time(remaining_time)} before starting another battle!")

    # Select a random anime arc
    selected_arc = random.choice(anime_arcs)

    # Set user cooldown
    user_cooldowns[user_id] = time.time()

    try:
        # Initial message with arc details
        start_message = (
            f"⚔️ **Anime Arc Battle** ⚔️\n\n**Arc:** {selected_arc['arc']}\n"
            f"**Heroes:** {', '.join([hero['name'] for hero in selected_arc['heroes']])}\n"
            f"**Villains:** {', '.join(selected_arc['villains'])}\n\n🌟 **Let the battle begin!**"
        )
        await bot.send_photo(chat_id, photo=selected_arc['image'], caption=start_message)

        # Simulate battle
        await asyncio.sleep(3)
        await message.reply_text("🌀 Heroes and Villains are clashing fiercely...")
        await asyncio.sleep(3)

        if random.random() < (win_rate_percentage / 100):
            # User wins, assign a random rarity and hero
            selected_rarity = random.choice(rarities)
            reward_character = random.choice(selected_arc['heroes'])
            reward_data = {
                "name": reward_character['name'],
                "anime": selected_arc['arc'],
                "rarity": selected_rarity,
                "img_url": reward_character['img_url'],
            }
            await user_collection.update_one(
                {"id": user_id}, {"$push": {"characters": reward_data}}
            )

            victory_message = (
                f"🎉 **Victory!**\n\n{mention}, you triumphed in the battle of **{selected_arc['arc']}**!\n\n"
                f"**🎖️ Reward:**\n"
                f"🏅 **Character:** {reward_character['name']}\n"
                f"⭐ **Rarity:** {selected_rarity}\n\nKeep battling for more rewards!"
            )
            await bot.send_photo(chat_id, photo=reward_character['img_url'], caption=victory_message)
        else:
            # User loses
            defeat_message = (
                f"💀 **Defeat!**\n\n{mention}, the villains overpowered you in the epic battle of "
                f"**{selected_arc['arc']}**. Don't give up; train harder and try again!"
            )
            await bot.send_photo(chat_id, photo=selected_arc['image'], caption=defeat_message)
    except Exception as e:
        print(f"Error: {e}")
        await message.reply_text("❗ An error occurred. Please try again later.")
