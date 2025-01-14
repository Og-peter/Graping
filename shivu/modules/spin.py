import asyncio
from pyrogram import filters, Client, types as t
from shivu import shivuu as bot
from shivu import collection, user_collection
import time
import random

# Cooldown and streak trackers
cooldowns = {}
streaks = {}
milestones = [5, 10, 20, 50]  # Milestone rewards

async def get_random_character(receiver_id, target_rarities=['🟡 Nobel', '🥵 Nudes']):
    try:
        user_data = await user_collection.find_one({'id': receiver_id}, {'characters': 1})
        owned_character_ids = [char['id'] for char in user_data.get('characters', [])] if user_data else []

        pipeline = [
            {'$match': {
                'rarity': {'$in': target_rarities},
                'id': {'$nin': owned_character_ids}
            }},
            {'$sample': {'size': 1}}
        ]
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=1)
        return characters
    except Exception as e:
        print(f"Error in get_random_character: {e}")
        return []

@bot.on_message(filters.command(["spin"]))
async def spin(_, message: t.Message):
    user_id = message.from_user.id
    mention = message.from_user.mention

    # Cooldown management
    if user_id in cooldowns and time.time() - cooldowns[user_id] < 60:
        cooldown_time = int(60 - (time.time() - cooldowns[user_id]))
        await message.reply_text(
            f"⏳ *Patience, {mention}!*\nYou can spin again in *{cooldown_time} seconds*.", quote=True
        )
        return

    # Update cooldown and animation
    cooldowns[user_id] = time.time()
    msg = await message.reply_text("🎰 **Spinning the wheel...** 🎰", quote=True)
    await asyncio.sleep(2)

    # Generate spin results
    spin_symbols = ["🍒", "💎", "⭐", "🍀", "🔥", "🌟", "⚡"]
    spin_result = random.choices(spin_symbols, k=3)
    formatted_result = f"🎰 | {spin_result[0]} | {spin_result[1]} | {spin_result[2]}"

    # Determine outcome
    outcomes = {
        "jackpot": 10,
        "epic": 30,
        "rare": 25,
        "common": 20,
        "bonus": 15
    }
    outcome = random.choices(list(outcomes.keys()), weights=outcomes.values(), k=1)[0]

    # Handle outcomes
    if outcome == "jackpot":
        random_characters = await get_random_character(user_id)
        if random_characters:
            character = random_characters[0]
            await user_collection.update_one(
                {'id': user_id}, {'$push': {'characters': character}}, upsert=True
            )
            character_image = character.get('image_url', None)
            if character_image:
                # Send character image with details
                await bot.send_photo(
                    chat_id=message.chat.id,
                    photo=character_image,
                    caption=(
                        f"🌟 **Name:** {character['name']}\n"
                        f"⚜️ **Rarity:** {character['rarity']}\n"
                        f"⛩️ **Anime:** {character['anime']}\n\n"
                        f"🎉 *JACKPOT!* {mention}, you've unlocked a *legendary* character!"
                    ),
                    reply_to_message_id=message.message_id
                )
            else:
                # Fallback if no image is available
                await msg.edit_text(
                    f"{formatted_result}\n\n🎉 *JACKPOT!* 🎉\n\n"
                    f"🌟 **Name:** {character['name']}\n"
                    f"⚜️ **Rarity:** {character['rarity']}\n"
                    f"⛩️ **Anime:** {character['anime']}\n\n"
                    f"Congratulations {mention}!"
                )
        else:
            await msg.edit_text(
                f"🎉 *JACKPOT!* 🎉\n\n{formatted_result}\n\n"
                f"⚠️ No new characters available! Check back later."
            )
        cooldowns[user_id] -= 30

    elif outcome == "epic":
        await msg.edit_text(
            f"✨ *EPIC WIN!* ✨\n\n{formatted_result}\n\n"
            f"🔥 Incredible, {mention}! You're getting closer to greatness!"
        )
        cooldowns[user_id] -= 20

    elif outcome == "rare":
        await msg.edit_text(
            f"🌟 *Rare Find!* 🌟\n\n{formatted_result}\n\n"
            f"🍀 Good job, {mention}! Rare combos are rewarding!"
        )
        cooldowns[user_id] -= 15

    elif outcome == "bonus":
        await msg.edit_text(
            f"🎁 *BONUS SPIN!* 🎁\n\n{formatted_result}\n\n"
            f"🔄 You've earned an extra spin, {mention}! Spin again now!"
        )
        cooldowns[user_id] = 0

    else:
        await msg.edit_text(
            f"💔 *No Luck This Time!* 💔\n\n{formatted_result}\n\n"
            f"🔄 Keep trying, {mention}! The big win is just around the corner!"
        )

    # Streak tracking
    streaks[user_id] = streaks.get(user_id, 0) + 1
    streak_msg = ""

    if streaks[user_id] in milestones:
        streak_msg = f"🎉 *Milestone!* 🎉\nYou've completed *{streaks[user_id]}* spins! 🎊"

    elif streaks[user_id] % 5 == 0:
        streak_msg = f"🔥 *Streak Bonus!* 🔥\nYou're on a streak of *{streaks[user_id]}* spins!"

    if streak_msg:
        await message.reply_text(streak_msg)
