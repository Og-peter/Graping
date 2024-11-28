import asyncio
from pyrogram import filters, Client, types as t
from shivu import shivuu as bot
from shivu import collection, user_collection
import time
import random

# Cooldown dictionary
cooldowns = {}

async def get_random_character(receiver_id, target_rarities=['🟡 Nobel', '🥵 Nudes']):
    try:
        # Fetch user characters to exclude already-owned ones
        user_data = await user_collection.find_one({'id': receiver_id}, {'characters': 1})
        owned_character_ids = [char['id'] for char in user_data.get('characters', [])] if user_data else []

        # MongoDB pipeline to fetch random characters
        pipeline = [
            {'$match': {
                'rarity': {'$in': target_rarities},
                'id': {'$nin': owned_character_ids}
            }},
            {'$sample': {'size': 1}}
        ]
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=1)

        # Return the fetched character, or an empty list if none are found
        return characters
    except Exception as e:
        print(f"Error in get_random_character: {e}")
        return []

@bot.on_message(filters.command(["spin"]))
async def spin(_, message: t.Message):
    user_id = message.from_user.id
    mention = message.from_user.mention

    # Cooldown check
    if user_id in cooldowns and time.time() - cooldowns[user_id] < 60:
        cooldown_time = int(60 - (time.time() - cooldowns[user_id]))
        await message.reply_text(
            f"⏳ Hold on {mention}, you can spin again in *{cooldown_time}* seconds.", 
            quote=True
        )
        return

    # Update cooldown
    cooldowns[user_id] = time.time()

    # Simulating the spin animation
    spin_animation = "🎰 Spinning... 🎰\n\n🔄 | 🔄 | 🔄"
    msg = await message.reply_text(spin_animation, quote=True)
    await asyncio.sleep(2)

    spin_symbols = ["🍒", "💎", "⭐", "🍀", "🔥"]  # Extended symbols for more variety
    spin_result = random.choices(spin_symbols, k=3)  # Generate three random symbols
    outcome = random.choice(["jackpot", "rare", "medium", "lose"])  # Randomized outcomes

    # Formatting the spin result
    formatted_result = f"🎰 | {spin_result[0]} | {spin_result[1]} | {spin_result[2]}"

    if outcome == "jackpot":
        # Jackpot case
        random_characters = await get_random_character(user_id)
        if random_characters:
            character = random_characters[0]
            await user_collection.update_one(
                {'id': user_id}, {'$push': {'characters': character}}, upsert=True
            )
            await msg.edit_text(
                f"{formatted_result}\n\n"
                f"🍃 **Name:** {character['name']}\n"
                f"⚜️ **Rarity:** {character['rarity']}\n"
                f"⛩️ **Anime:** {character['anime']}\n\n"
                f"🌟 Congratulations {mention}, you unlocked a *legendary* character!"
            )
        else:
            await msg.edit_text(
                f"🎉 *JACKPOT!* 🎉\n\n{formatted_result}\n\n"
                f"⚠️ No new characters available to unlock! Check your collection or try again later."
            )

    elif outcome == "rare":
        # Rare win case
        await msg.edit_text(
            f"✨ *RARE FIND!* ✨\n\n"
            f"{formatted_result}\n\n"
            f"🍀 Incredible spin, {mention}! You got a rare combo! Keep it up!"
        )

    elif outcome == "medium":
        # Medium win case
        await msg.edit_text(
            f"🌟 *Nice Spin!* 🌟\n\n"
            f"{formatted_result}\n\n"
            f"💎 Great effort, {mention}! You're getting closer to the big win!"
        )

    else:
        # Lose case
        await msg.edit_text(
            f"💔 *Better Luck Next Time!* 💔\n\n"
            f"{formatted_result}\n\n"
            f"🔄 Don't lose hope, {mention}! Spin again to hit the jackpot!"
        )

    # Adding a final encouragement
    await asyncio.sleep(1)
    await message.reply_text(
        f"🎲 Ready for another spin, {mention}? Who knows, *fortune* might be on your side next!"
            )
