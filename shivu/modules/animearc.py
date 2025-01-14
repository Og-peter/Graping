import asyncio
import random
import time
from pyrogram import filters, Client, types as t
from shivu import shivuu as bot
from shivu import user_collection, collection

# Configuration
win_rate_percentage = 50  # Probability of winning
cooldown_duration = 600  # Cooldown time in seconds

user_cooldowns = {}
ban_user_ids = {1234567890}

# Anime Arc Data with Expanded Features
anime_arcs = [
    {
        "arc": "Naruto - Pain's Assault",
        "heroes": [
            {"name": "Naruto Uzumaki", "img_url": "https://files.catbox.moe/1naruto.jpg"},
            {"name": "Kakashi Hatake", "img_url": "https://files.catbox.moe/1kakashi.jpg"},
        ],
        "villains": [
            {"name": "Pain", "img_url": "https://files.catbox.moe/1pain.jpg"},
            {"name": "Konan", "img_url": "https://files.catbox.moe/1konan.jpg"},
        ],
        "battle_image": "https://files.catbox.moe/83rsnb.jpg",
    },
    {
        "arc": "One Piece - Marineford War",
        "heroes": [
            {"name": "Monkey D. Luffy", "img_url": "https://files.catbox.moe/1luffy.jpg"},
            {"name": "Whitebeard", "img_url": "https://files.catbox.moe/1whitebeard.jpg"},
        ],
        "villains": [
            {"name": "Akainu", "img_url": "https://files.catbox.moe/1akainu.jpg"},
            {"name": "Blackbeard", "img_url": "https://files.catbox.moe/1blackbeard.jpg"},
        ],
        "battle_image": "https://files.catbox.moe/urb2aa.jpg",
    },
]

rarities = ['🔵 Common', '🟢 Rare', '🔴 Epic', '🟡 Legendary', '🔮 Mythical']

# Helper Functions
def human_readable_time(seconds: int) -> str:
    mins, secs = divmod(seconds, 60)
    return f"{mins}m {secs}s" if mins else f"{secs}s"

def get_random_event() -> str:
    events = [
        "⚡ A sudden lightning strike empowers the heroes!",
        "🔥 The villains unleash a devastating attack!",
        "🌀 A mysterious force alters the battle's tide!",
        "💪 Heroes gain unexpected reinforcements!",
    ]
    return random.choice(events)

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
        return await message.reply_text(
            f"⏳ Please wait {human_readable_time(remaining_time)} before attempting another battle!"
        )

    # Select a random arc
    selected_arc = random.choice(anime_arcs)
    user_cooldowns[user_id] = time.time()

    try:
        # Start battle
        start_message = (
            f"⚔️ **Anime Arc Battle** ⚔️\n\n"
            f"**Arc:** {selected_arc['arc']}\n\n"
            f"**Heroes:** {', '.join([hero['name'] for hero in selected_arc['heroes']])}\n"
            f"**Villains:** {', '.join([villain['name'] for villain in selected_arc['villains']])}\n\n"
            f"🌌 **The epic battle begins! Brace yourself, {mention}!**"
        )
        await bot.send_photo(chat_id, photo=selected_arc['battle_image'], caption=start_message)

        await asyncio.sleep(3)

        # Simulate phases of battle
        for i in range(2):  # 2 phases
            event = get_random_event()
            await message.reply_text(f"🌀 Phase {i + 1}: {event}")
            await asyncio.sleep(3)

        # Determine outcome
        if random.random() < (win_rate_percentage / 100):
            # Victory
            selected_rarity = random.choice(rarities)
            reward_character = random.choice(selected_arc['heroes'])
            reward_data = {
                "name": reward_character["name"],
                "anime": selected_arc["arc"],
                "rarity": selected_rarity,
                "img_url": reward_character["img_url"],
            }
            await user_collection.update_one(
                {"id": user_id}, {"$push": {"characters": reward_data}}
            )

            victory_message = (
                f"🎉 **Victory!**\n\n"
                f"{mention}, you emerged victorious in the **{selected_arc['arc']}** battle!\n\n"
                f"🏅 **Reward:**\n"
                f"🎭 **Character:** {reward_character['name']}\n"
                f"⭐ **Rarity:** {selected_rarity}\n\n"
                f"💾 **Character added to your collection!**"
            )
            await bot.send_photo(chat_id, photo=reward_character["img_url"], caption=victory_message)
        else:
            # Defeat
            defeat_message = (
                f"💀 **Defeat!**\n\n"
                f"The villains triumphed in the battle of **{selected_arc['arc']}**. Don't give up, {mention}! "
                f"Prepare for your next epic encounter!"
            )
            await bot.send_photo(chat_id, photo=selected_arc['battle_image'], caption=defeat_message)
    except Exception as e:
        print(f"Error: {e}")
        await message.reply_text("❗ An error occurred during the battle. Please try again later.")
