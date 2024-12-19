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

# Battle confirmation callback
@bot.on_callback_query(filters.regex(r"battle_confirm\|(\d+)\|(\d+)"))
async def battle_confirmation(client: Client, callback_query: t.CallbackQuery):
    challenger_id, opponent_id = map(int, callback_query.data.split("|")[1:])
    user = callback_query.from_user

    if user.id != opponent_id:
        return await callback_query.answer("⚠️ Only the opponent can confirm this battle!", show_alert=True)

    await callback_query.answer()

    # Start battle sequence
    challenger = await bot.get_users(challenger_id)
    opponent = await bot.get_users(opponent_id)

    challenger_move = random.choice(list(CHARACTERS.items()))
    opponent_move = random.choice(list(CHARACTERS.items()))

    # Send moves with videos
    await bot.send_video(
        chat_id=callback_query.message.chat.id,
        video=challenger_move[1]['video_url'],
        caption=f"**{challenger.first_name} uses:** {challenger_move[1]['move']}"
    )
    await asyncio.sleep(2)
    await bot.send_video(
        chat_id=callback_query.message.chat.id,
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
        await bot.send_photo(
            chat_id=callback_query.message.chat.id,
            photo=random_characters[0]['img_url'],
            caption=reward_message
        )
    else:
        await bot.send_message(
            chat_id=callback_query.message.chat.id,
            text="⚠️ **Something went wrong while fetching the reward. Please try again later.**"
        )

    # Send a message about the loss
    await bot.send_message(
        chat_id=callback_query.message.chat.id,
        text=f"💀 **{loser.first_name} loses the battle. Better luck next time!**"
    )

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

    # Send confirmation button
    confirm_markup = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("✅ Confirm", callback_data=f"battle_confirm|{challenger.id}|{opponent.id}"),
            InlineKeyboardButton("❌ Reject", callback_data="battle_reject")
        ]]
    )
    await message.reply_text(
        f"⚔️ **{challenger.first_name} has challenged {opponent.first_name} to a battle!**\n\n"
        f"🔹 {opponent.first_name}, please confirm or reject the challenge below:",
        reply_markup=confirm_markup
    )
