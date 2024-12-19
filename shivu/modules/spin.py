import asyncio
from pyrogram import filters, Client, types as t
from shivu import shivuu as bot
from shivu import collection, user_collection
import time
import random

# Cooldown dictionary and streak tracker
cooldowns = {}
streaks = {}

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

    # Spin animation
    spin_animation = "🎰 Spinning... 🎰\n\n🔄 | 🔄 | 🔄"
    msg = await message.reply_text(spin_animation, quote=True)
    await asyncio.sleep(2)

    # Generate spin results
    spin_symbols = ["🍒", "💎", "⭐", "🍀", "🔥", "🌟", "⚡"]
    spin_result = random.choices(spin_symbols, k=3)
    outcome = random.choice(["jackpot", "rare", "medium", "lose", "bonus"])

    formatted_result = f"🎰 | {spin_result[0]} | {spin_result[1]} | {spin_result[2]}"

    # Handle outcomes
    if outcome == "jackpot":
        random_characters = await get_random_character(user_id)
        if random_characters:
            character = random_characters[0]
            
            # Add character to user's collection
            await user_collection.update_one(
                {'id': user_id}, {'$push': {'characters': character}}, upsert=True
            )
            
            # Send character image with details
            character_image = character.get('image_url', None)
            if character_image:
                await bot.send_photo(
                    chat_id=message.chat.id,
                    photo=character_image,
                    caption=(
                        f"🌟 **Name:** {character['name']}\n"
                        f"⚜️ **Rarity:** {character['rarity']}\n"
                        f"⛩️ **Anime:** {character['anime']}\n\n"
                        f"🎉 Congratulations {mention}, you unlocked a *legendary* character!"
                    ),
                    reply_to_message_id=message.message_id
                )
            else:
                # Fallback if no image is available
                await msg.edit_text(
                    f"{formatted_result}\n\n"
                    f"🌟 **Name:** {character['name']}\n"
                    f"⚜️ **Rarity:** {character['rarity']}\n"
                    f"⛩️ **Anime:** {character['anime']}\n\n"
                    f"🎉 Congratulations {mention}, you unlocked a *legendary* character!"
                )
        else:
            await msg.edit_text(
                f"🎉 *JACKPOT!* 🎉\n\n{formatted_result}\n\n"
                f"⚠️ No new characters available! Check your collection or try again later."
            )
        cooldowns[user_id] -= 30  # Reduce cooldown for jackpot

    elif outcome == "rare":
        await msg.edit_text(
            f"✨ *RARE FIND!* ✨\n\n"
            f"{formatted_result}\n\n"
            f"🍀 Great spin, {mention}! Rare combos are hard to hit!"
        )
        cooldowns[user_id] -= 15  # Reduce cooldown for rare finds

    elif outcome == "medium":
        await msg.edit_text(
            f"🌟 *Nice Spin!* 🌟\n\n"
            f"{formatted_result}\n\n"
            f"💎 Good effort, {mention}! You're on the right path!"
        )

    elif outcome == "bonus":
        await msg.edit_text(
            f"🎁 *BONUS!* 🎁\n\n"
            f"{formatted_result}\n\n"
            f"🔑 {mention}, you've won a *bonus spin*! Use it wisely!"
        )
        cooldowns[user_id] = 0  # Reset cooldown for bonus spin

    else:
        await msg.edit_text(
            f"💔 *Better Luck Next Time!* 💔\n\n"
            f"{formatted_result}\n\n"
            f"🔄 Keep trying, {mention}! The jackpot awaits!"
        )

    # Update streak count
    streaks[user_id] = streaks.get(user_id, 0) + 1
    if streaks[user_id] % 5 == 0:
        await message.reply_text(
            f"🔥 *Amazing!* 🔥\n\n"
            f"{mention}, you've completed a streak of *{streaks[user_id]}* spins!"
            )
