import asyncio
import random
import time
from pyrogram import filters, Client, types as t
from shivu import shivuu as bot
from shivu import user_collection, collection

win_rate_percentage = 30  # Adjust the win rate percentage
cooldown_duration = 60  # Cooldown duration in seconds

user_cooldowns = {}  # To track user cooldowns
ban_user_ids = {1234567890}  # List of banned users

async def get_random_characters(rarity):
    """Fetch random characters based on rarity."""
    try:
        pipeline = [
            {'$match': {'rarity': rarity}},
            {'$sample': {'size': 1}}
        ]
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)
        return characters
    except Exception as e:
        print(f"Error fetching characters: {e}")
        return []

@bot.on_message(filters.command(["spin"]))
async def spin(_, message: t.Message):
    user_id = message.from_user.id
    mention = message.from_user.mention

    # Check if the user is banned
    if user_id in ban_user_ids:
        return await message.reply_text("🚫 You are banned from using this command. Contact support for assistance.")

    # Check cooldown
    if user_id in user_cooldowns and time.time() - user_cooldowns[user_id] < cooldown_duration:
        remaining_time = cooldown_duration - int(time.time() - user_cooldowns[user_id])
        return await message.reply_text(
            f"⏳ Please wait! Your spin will be ready in **{remaining_time} seconds**."
        )

    # Set cooldown
    user_cooldowns[user_id] = time.time()

    # Spinning animation
    spinning_messages = [
        "🔄 Spinning the wheel... 🎡",
        "🎰 Rolling the luck dice...",
        "✨ Determining your fortune...",
    ]
    spin_message = await message.reply_text(random.choice(spinning_messages))
    await asyncio.sleep(2)

    # Determine win/loss
    if random.random() < (win_rate_percentage / 100):
        # User wins
        rarity = random.choice(['🔵 Low', '🟢 Medium', '🟣 High', '🟡 Nobel'])
        characters = await get_random_characters(rarity)

        if characters:
            char = characters[0]
            img_url = char['img_url']
            caption = (
                f"🎉 **Congratulations, {mention}!** 🎉\n"
                f"You just won a character! ✨\n\n"
                f"📝 **Name:** {char['name']}\n"
                f"🌟 **Rarity:** {char['rarity']}\n"
                f"🎥 **Anime:** {char['anime']}\n\n"
                f"💎 **Enjoy your prize!**"
            )

            # Send the character details with an image
            await spin_message.delete()
            await message.reply_photo(photo=img_url, caption=caption)

            # Add character to user's collection
            await user_collection.update_one(
                {'id': user_id},
                {'$push': {'characters': char}}
            )

            # Random chance for bonus coins
            if random.random() < 0.5:
                bonus_coins = random.randint(50, 200)
                await message.reply_text(
                    f"💰 Bonus Alert! You've also won **{bonus_coins} coins**. Keep spinning for more rewards!"
                )
        else:
            await spin_message.edit("⚠️ Oops! Something went wrong. No characters were found for this rarity.")
    else:
        # User loses
        lose_messages = [
            "💔 You didn't win this time. Better luck next spin!",
            "😢 No character this time, but keep trying!",
            "🌀 The wheel wasn't in your favor. Spin again soon!"
        ]
        await spin_message.edit(random.choice(lose_messages))

    # Cool visual end animation
    await asyncio.sleep(1)
    await message.reply_text("🔔 **Spin completed!** Try again later.")
