import asyncio
import random
import time
from pyrogram import filters, Client, types as t
from shivu import shivuu as bot
from shivu import user_collection, collection

WIN_RATE_PERCENTAGE = 30  # Win rate percentage
COOLDOWN_DURATION = 60  # Cooldown duration in seconds
user_cooldowns = {}  # Dictionary to track user cooldowns

# List of banned user IDs
BAN_USER_IDS = {1234567890}

# Fetch random character based on rarity
async def get_random_characters(selected_rarity):
    try:
        pipeline = [
            {'$match': {'rarity': selected_rarity}},
            {'$sample': {'size': 1}}
        ]
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)
        return characters
    except Exception as e:
        print(e)
        return []

@bot.on_message(filters.command(["spin"]))
async def spin(_: bot, message: t.Message):
    chat_id = message.chat.id
    mention = message.from_user.mention
    user_id = message.from_user.id

    # Check if user is banned
    if user_id in BAN_USER_IDS:
        return await message.reply_text("🚫 You are banned from using this command. Please contact support.")

    # Check cooldown
    if user_id in user_cooldowns and time.time() - user_cooldowns[user_id] < COOLDOWN_DURATION:
        remaining_time = COOLDOWN_DURATION - int(time.time() - user_cooldowns[user_id])
        return await message.reply_text(f"⏳ Please wait! Your spin will be ready in **{remaining_time} seconds**.")

    # Set cooldown
    user_cooldowns[user_id] = time.time()

    # Spinning animation
    spinning_message = "🎡 **The wheel is turning... 🔥**"
    progress_bar = ["🌑"] * 10  # Initial empty progress bar
    msg = await message.reply_text(f"{spinning_message}\nSpinning: [{''.join(progress_bar)}]")

    # Simulate progress bar animation
    for i in range(10):
        progress_bar[i] = "🌕"  # Update progress
        await asyncio.sleep(0.3)  # Delay for smooth animation
        await msg.edit_text(f"{spinning_message}\nSpinning: [{''.join(progress_bar)}]")

    # Final spin reveal animation
    await asyncio.sleep(0.5)
    await msg.edit_text(f"🎊 **The wheel is slowing down... 🌀**")
    await asyncio.sleep(1)

    # Check win or lose
    if random.random() < (WIN_RATE_PERCENTAGE / 100):
        # Winning case
        selected_rarity = random.choice(['🔵 Low', '🟢 Medium', '🟣 High', '🟡 Nobel'])
        random_characters = await get_random_characters(selected_rarity)

        if random_characters:
            img_urls = [character['img_url'] for character in random_characters]
            captions = [
                f"✨ **Congratulations {mention}!** 🎉\n\n"
                f"🏆 **Character Name:** {character['name']}\n"
                f"🔮 **Rarity:** {character['rarity']}\n"
                f"📺 **Anime:** {character['anime']}\n\n"
                f"💖 Keep spinning for more amazing rewards!"
                for character in random_characters
            ]

            for img_url, caption in zip(img_urls, captions):
                await message.reply_photo(photo=img_url, caption=caption)

            # Add character to user's collection
            for character in random_characters:
                await user_collection.update_one({'id': user_id}, {'$push': {'characters': character}})
        else:
            await msg.edit_text("❗ Something went wrong. Please try again later.")
    else:
        # Losing case
        await msg.edit_text(
            f"💔 **Better luck next time, {mention}!**\n\n"
            f"🌟 Keep trying! Your fortune might change in the next spin."
            )
