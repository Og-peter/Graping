import asyncio
import random
import time
from pyrogram import filters, Client, types as t
from shivu import shivuu as bot
from shivu import user_collection, collection

# Configurable Parameters
win_rate_percentage = 40  # Win rate percentage
cooldown_duration = 60  # Cooldown duration (in seconds)
max_spins = 3  # Maximum spins allowed per use

user_cooldowns = {}  # Tracks cooldowns for users
ban_user_ids = {1234567890}  # List of banned user IDs


async def get_random_characters(selected_rarity):
    """Fetches a random character based on rarity."""
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
async def spin(_, message: t.Message):
    chat_id = message.chat.id
    mention = message.from_user.mention
    user_id = message.from_user.id

    # Check if user is banned
    if user_id in ban_user_ids:
        return await message.reply_text(
            "🚫 You are banned from using this command. Contact support for assistance."
        )

    # Check if user is on cooldown
    if user_id in user_cooldowns and time.time() - user_cooldowns[user_id] < cooldown_duration:
        remaining_time = cooldown_duration - int(time.time() - user_cooldowns[user_id])
        return await message.reply_text(
            f"⏳ Please wait! Your spin is cooling down for **{remaining_time} seconds**."
        )

    # Set user cooldown
    user_cooldowns[user_id] = time.time()

    # Start the spinning process
    await message.reply_text("🎡 **Spinning the wheel...** 🔄")
    await asyncio.sleep(2)  # Add suspense with a delay

    progress_bar = "🔘🔘🔘🔘🔘"  # Progress bar
    progress_text = f"🔄 **Progress:** {progress_bar}\n\nKeep watching!"
    progress_message = await message.reply_text(progress_text)

    # Simulate progress updates
    for i in range(5):
        await asyncio.sleep(1)  # Delay for each update
        progress_bar = progress_bar.replace("🔘", "🟢", 1)
        progress_text = f"🔄 **Progress:** {progress_bar}\n\nStay tuned!"
        await progress_message.edit_text(progress_text)

    # Simulate multiple spins
    results = []
    for spin in range(1, max_spins + 1):
        if random.random() < (win_rate_percentage / 100):
            rarity = random.choice(['🔵 Low', '🟢 Medium', '🟣 High', '🟡 Nobel'])
            characters = await get_random_characters(rarity)
            if characters:
                for character in characters:
                    results.append({
                        "name": character['name'],
                        "rarity": character['rarity'],
                        "anime": character['anime'],
                        "img_url": character['img_url']
                    })
                    # Save to user collection
                    await user_collection.update_one(
                        {'id': user_id},
                        {'$push': {'characters': character}},
                        upsert=True
                    )
            else:
                results.append({"error": f"No character found for rarity {rarity}"})
        else:
            results.append({"error": "No win this time"})

    # Build results message
    final_message = "**🎉 Spin Results!**\n\n"
    for i, result in enumerate(results, 1):
        if "error" in result:
            final_message += f"🔹 Spin {i}: {result['error']} 💔\n"
        else:
            final_message += (
                f"🔹 Spin {i}: **{result['name']}**\n"
                f"    Rarity: {result['rarity']}\n"
                f"    Anime: {result['anime']}\n"
            )

    # Send final message and images
    if results:
        await progress_message.delete()  # Clean up progress message
        await message.reply_text(final_message)

        # Send images
        for result in results:
            if "img_url" in result:
                await message.reply_photo(
                    photo=result["img_url"],
                    caption=f"🎉 **You Won!**\n"
                            f"**Name:** {result['name']}\n"
                            f"**Rarity:** {result['rarity']}\n"
                            f"**Anime:** {result['anime']}"
                )
    else:
        await message.reply_text("💔 No rewards this time. Try again later!")

    # Cooldown message
    await asyncio.sleep(cooldown_duration)
    await message.reply_text(f"✅ Your spin cooldown is over, {mention}! You can spin again.")
