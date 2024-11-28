import asyncio
import random
import time
from pyrogram import filters, Client, types as t
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shivu import shivuu as bot
from shivu import user_collection, collection

# Constants
WIN_REWARD_CHARACTER_COUNT = 1  # Number of characters a winner gets
COOLDOWN_DURATION = 300  # Cooldown duration in seconds (5 minutes)

# Cooldown tracker
user_cooldowns = {}

# Anime characters' best forms and videos
CHARACTERS = {
    "Saitama": {
        "move": "🔥 **Saitama delivers a 'Serious Punch' and obliterates the battlefield!**",
        "video_url": "https://files.catbox.moe/rw2yuz.mp4"
    },
    "Goku": {
        "move": "🌌 **Goku unleashes 'Ultra Instinct Kamehameha', shaking the universe!**",
        "video_url": "https://files.catbox.moe/90bga6.mp4"
    },
    "Naruto": {
        "move": "🌀 **Naruto activates 'Baryon Mode' and overwhelms the opponent!**",
        "video_url": "https://files.catbox.moe/d2iygy.mp4"
    },
    "Luffy": {
        "move": "🌊 **Luffy goes 'Gear 5', turning the fight into cartoon chaos!**",
        "video_url": "https://files.catbox.moe/wmc671.gif"
    },
    "Ichigo": {
        "move": "⚡ **Ichigo transforms into 'Final Getsuga Tenshou', slashing everything!**",
        "video_url": "https://files.catbox.moe/ky17sr.mp4"
    },
    "Madara": {
        "move": "🌪️ **Madara casts 'Perfect Susanoo', decimating the battlefield!**",
        "video_url": "https://files.catbox.moe/lknesv.mp4"
    },
    "Aizen": {
        "move": "💀 **Aizen enters 'Hogyoku Form' and uses 'Kyoka Suigetsu' to confuse his enemy!**",
        "video_url": "https://files.catbox.moe/jv25db.mp4"
    },
}

# Function to get random characters as rewards
async def get_random_characters():
    try:
        pipeline = [
            {'$match': {'rarity': '🟡 Nobel'}},  # Adjust rarity as needed
            {'$sample': {'size': WIN_REWARD_CHARACTER_COUNT}}
        ]
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)
        return characters
    except Exception as e:
        print(f"Error fetching characters: {e}")
        return []

# Battle command handler
@bot.on_message(filters.command(["battle"]))
async def battle(_, message: t.Message):
    if not message.reply_to_message:
        return await message.reply_text("⚠️ **Reply to another user to challenge them to a battle!**")
    
    challenger = message.from_user
    opponent = message.reply_to_message.from_user

    # Check if the opponent is the bot itself
    if opponent.is_bot:
        return await message.reply_text("🤖 **You can't battle against the bot! Challenge another user instead.**")

    # Check if the challenger is replying to their own message
    if challenger.id == opponent.id:
        return await message.reply_text("⚠️ **You can't battle against yourself. Challenge someone else!**")

    # Cooldown check for the challenger
    current_time = time.time()
    if challenger.id in user_cooldowns and current_time - user_cooldowns[challenger.id] < COOLDOWN_DURATION:
        return await message.reply_text("⏳ **You need to wait before challenging someone again.**")

    # Start battle sequence
    challenger_move = random.choice(list(CHARACTERS.items()))
    opponent_move = random.choice(list(CHARACTERS.items()))

    # Send moves with videos
    await message.reply_video(
        video=challenger_move[1]['video_url'],
        caption=f"**{challenger.first_name} uses:** {challenger_move[1]['move']}"
    )
    await asyncio.sleep(2)
    await message.reply_video(
        video=opponent_move[1]['video_url'],
        caption=f"**{opponent.first_name} counters with:** {opponent_move[1]['move']}"
    )
    await asyncio.sleep(2)

    # Decide the winner
    winner = random.choice([challenger, opponent])
    loser = challenger if winner == opponent else opponent

    # Reward the winner
    random_characters = await get_random_characters()
    if random_characters:
        for character in random_characters:
            await user_collection.update_one(
                {'id': winner.id}, {'$push': {'characters': character}}
            )

        reward_message = (
            f"🏆 **{winner.first_name} wins the battle!**\n\n"
            f"🎁 **Reward:**\n"
        )
        for character in random_characters:
            reward_message += (
                f"🍁 **Name:** {character['name']}\n"
                f"🥂 **Rarity:** {character['rarity']}\n"
                f"⛩️ **Anime:** {character['anime']}\n\n"
            )
        await message.reply_photo(
            photo=random_characters[0]['img_url'],
            caption=reward_message
        )
    else:
        await message.reply_text("⚠️ **Something went wrong while fetching the reward. Please try again later.**")

    # Send a message about the loss
    await message.reply_text(f"💀 **{loser.first_name} loses the battle. Better luck next time!**")

    # Set cooldown for the challenger
    user_cooldowns[challenger.id] = current_time
