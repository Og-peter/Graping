from telegram.ext import CommandHandler
from shivu import application, registered_users,SUPPORT_CHAT
from telegram import Update
from datetime import datetime, timedelta
import asyncio
import time
import random
import html
from datetime import datetime, timedelta
from shivu import shivuu as bot
from shivu import shivuu as app
from pyrogram.types import Message
from pyrogram import filters, types as t
from html import escape
from shivu import application, user_collection
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler, ContextTypes
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from shivu import sudo_users_collection, user_collection
from shivu.modules.database.sudo import is_user_sudo

cooldowns = {}
user_last_command_times = {}
ban_user_ids = {5553813115}
logs_group_id = -1001992198513
logs = {logs_group_id}
async def send_start_button(chat_id):
    await app.send_message(
        chat_id,
        "🔔 **Welcome!**\n\nTo register, you need to start the bot in private chat. Simply click the **Start** button below to begin your journey!",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Start", url=f"https://t.me/Grap_Waifu_Bot?start=start")]]
        )
    )


@app.on_message(filters.command(["sinv", "balance", "bal", "wealth"]))
async def check_balance(_, message: Message):
    user_id = message.from_user.id
    replied_user_id = None

    if message.reply_to_message:
        replied_user_id = message.reply_to_message.from_user.id

    # Use the replied user's ID if the command is a reply
    if replied_user_id:
        user_id = replied_user_id

    # Fetch user data from the database
    user_data = await user_collection.find_one({'id': user_id})
    if not user_data:
        await send_start_button(message.chat.id)
        return

    # Retrieve and format balance
    balance = user_data.get('balance', 0)
    formatted_balance = "{:,.0f}".format(balance)
    first_name = user_data.get('first_name', 'User')

    # Generate dynamic responses with video URL
    video_url = "https://files.catbox.moe/yveko5.mp4"
    responses = [
        f"💰 *{first_name}'s Treasury*: ₩`{formatted_balance}`\n[.]({video_url})",
        f"🌟 *{first_name}*, your fortune is ₩`{formatted_balance}`!\n[.]({video_url})",
        f"📊 Wealth report for *{first_name}*: ₩`{formatted_balance}`\n[.]({video_url})",
        f"🏦 *{first_name}'s Vault*: ₩`{formatted_balance}`\n[.]({video_url})",
        f"✨ *{first_name}*, your account sparkles with ₩`{formatted_balance}`.\n[.]({video_url})"
    ]
    unique_message = random.choice(responses)

    # Reply with the dynamic balance message
    await message.reply_text(unique_message, disable_web_page_preview=False)
    
# Command: Pay
async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender_id = update.effective_user.id

    # Custom help keyboard
    support_keyboard = [
        [InlineKeyboardButton("📩 Appeal Support", url="https://t.me/dynamic_gangs")]
    ]
    support_markup = InlineKeyboardMarkup(support_keyboard)

    # Cooldown check (20 minutes)
    if sender_id in cooldowns and (time.time() - cooldowns[sender_id]) < 1200:
        remaining_time = int(1200 - (time.time() - cooldowns[sender_id]))
        await update.message.reply_text(
            f"⏳ You can use /pay again in {remaining_time // 60} minutes and {remaining_time % 60} seconds.\n"
            "If you need help, click the button below.",
            reply_markup=support_markup,
        )
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Please reply to the user you want to pay.")
        return

    # Extract recipient ID and payment amount
    recipient_id = update.message.reply_to_message.from_user.id
    try:
        amount = int(context.args[0])
        if amount <= 0:
            raise ValueError("Amount must be positive.")
    except (IndexError, ValueError):
        await update.message.reply_text("🚫 Invalid amount. Use: /pay <amount>")
        return

    # Payment limit validation
    if amount > 1_000_000_000:
        await update.message.reply_text("💸 You can't pay more than ₩1,000,000,000.")
        return

    # Sender balance check
    sender_data = await user_collection.find_one({'id': sender_id}, projection={'balance': 1})
    if not sender_data or sender_data.get('balance', 0) < amount:
        await update.message.reply_text("❌ You don't have enough balance for this transaction.")
        return

    # Check for disallowed words in the command
    disallowed_words = ['negative', 'badword']  # Add any disallowed words here
    if any(word in update.message.text.lower() for word in disallowed_words):
        await update.message.reply_text("🚫 Your message contains disallowed words. Please try again.")
        return

    # Process the payment
    await user_collection.update_one({'id': sender_id}, {'$inc': {'balance': -amount}})
    await user_collection.update_one({'id': recipient_id}, {'$inc': {'balance': amount}})
    cooldowns[sender_id] = time.time()  # Set cooldown for the sender

    # Fetch recipient details
    recipient = await context.bot.get_chat(recipient_id)
    recipient_name = recipient.first_name + (f" {recipient.last_name}" if recipient.last_name else "")
    recipient_username = f"@{recipient.username}" if recipient.username else "an anonymous user"

    # Success message with image
    new_balance = sender_data['balance'] - amount
    success_message = (
        f"✅ <b>Transaction Successful!</b>\n"
        f"💳 You sent <b>₩{amount:,}</b> to <b>{recipient_name}</b> ({recipient_username}).\n"
        f"🔢 <b>Your New Balance:</b> <code>₩{new_balance:,}</code>\n"
        "💰 Thank you for using our service!"
    )
    await update.message.reply_photo(
        photo="https://files.catbox.moe/b861sv.jpg",  # Replace with your actual success image URL
        caption=success_message,
        parse_mode=ParseMode.HTML
    )

    # Notify the recipient
    recipient_message = (
        f"🎉 <b>You've received a payment!</b>\n"
        f"💸 Amount: <b>₩{amount:,}</b>\n"
        f"👤 From: <b>{update.effective_user.first_name}</b> "
        f"({f'@{update.effective_user.username}' if update.effective_user.username else 'an anonymous user'})\n"
        f"💰 Check your balance now!"
    )
    try:
        await context.bot.send_message(recipient_id, recipient_message, parse_mode=ParseMode.HTML)
    except Exception:
        # If the recipient can't be notified
        await update.message.reply_text("⚠️ Payment was successful, but the recipient could not be notified.")

# Summary of Changes:
# 1. **Image Only for Successful Payments**:
#    - An image is sent *only* after a successful payment. All other messages (errors or warnings) are plain text.
# 2. **Improved Error Messages**:
#    - Friendly, concise, and clear messages for errors like insufficient balance or invalid input.
# 3. **User-Friendly Messaging**:
#    - Clean formatting for amounts and clear descriptions for users.
            
async def mtop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Fetch top 10 users sorted by balance in descending order
    top_users = await user_collection.find(
        {}, 
        projection={'id': 1, 'first_name': 1, 'last_name': 1, 'balance': 1}
    ).sort('balance', -1).limit(10).to_list(10)

    # Header for the leaderboard
    top_users_message = (
        "🏅 <b>Top 10 Richest Users</b> 🏅\n"
        "💰 <i>Who’s ruling the leaderboard?</i>\n\n"
    )

    # List users with rank, name, and balance
    if not top_users:
        top_users_message += "❌ <i>No users found in the database.</i>"
    else:
        for i, user in enumerate(top_users, start=1):
            user_id = user.get('id', 'Unknown')
            first_name = html.escape(user.get('first_name', 'Unknown'))
            last_name = html.escape(user.get('last_name', '')) if user.get('last_name') else ''
            full_name = f"{first_name} {last_name}".strip()
            user_link = f"<a href='tg://user?id={user_id}'>{first_name}</a>"
            balance = user.get('balance', 0)
            top_users_message += f"❖ <b>{i}. {user_link}</b> — ₩{balance:,.0f}\n"

    # Footer
    top_users_message += "\n━━━━━━━━━━━━━━━━━\n<i>Stay active to secure your spot!</i>"

    # Send the leaderboard as a plain message
    await update.message.reply_text(
        text=top_users_message,
        parse_mode='HTML'
    )
    
@bot.on_message(filters.command("daily"))
async def daily_reward(_, message):
    user_id = message.from_user.id
    
    # Fetch user data
    user_data = await user_collection.find_one({'id': user_id}, projection={'last_daily_reward': 1, 'balance': 1})
    
    # If the user is not found in the database, prompt them to start/register
    if not user_data:
        await send_start_button(message.chat.id)
        return
    
    last_claimed_date = user_data.get('last_daily_reward')
    
    # Check if the user has already claimed the reward today
    if last_claimed_date and last_claimed_date.date() == datetime.utcnow().date():
        await message.reply_text("You've already claimed your daily reward today. Come back tomorrow!")
        return
    
    # Update the user's balance and set the last claimed date
    await user_collection.update_one(
        {'id': user_id},
        {'$inc': {'balance': 50000}, '$set': {'last_daily_reward': datetime.utcnow()}}
    )
    
    # Send an initial message and update it with animation-like edits
    msg = await message.reply_text("❰ 𝗥 𝗘 𝗪 𝗔 𝗥 𝗗 𝗦 🧧 ❱\n\nClaiming your reward...")
    await asyncio.sleep(2)
    await msg.edit_text("❰ 𝗥 𝗘 𝗪 𝗔 𝗥 𝗗 𝗦 🧧 ❱\n\n◍ **Processing reward...**")
    await asyncio.sleep(2)
    await msg.edit_text(
        "❰ 𝗥 𝗘 𝗪 𝗔 𝗥 𝗗 𝗦 🧧 ❱\n\n"
        "◍ **Daily reward claimed successfully!**\n"
        "You gained ₩`50,000` 🎉\n\n"
        "Come back tomorrow for more rewards!"
    )
    
@bot.on_message(filters.command("weekly"))
async def weekly_reward(_, message):
    user_id = message.from_user.id
    
    # Fetch user data
    user_data = await user_collection.find_one({'id': user_id}, projection={'last_weekly_reward': 1, 'balance': 1})
    
    # If the user is not found in the database, prompt them to start/register
    if not user_data:
        await send_start_button(message.chat.id)
        return
    
    last_weekly_date = user_data.get('last_weekly_reward')
    
    # Check if the user has already claimed the reward this week
    if last_weekly_date and last_weekly_date.date() == datetime.utcnow().date():
        await message.reply_text("You've already claimed your weekly reward of this week.")
        return
    
    # Update the user's balance and set the last claimed date
    await user_collection.update_one(
        {'id': user_id},
        {'$inc': {'balance': 250000}, '$set': {'last_weekly_reward': datetime.utcnow()}}
    )
    
    # Send an initial message and update it with animation-like edits
    msg = await message.reply_text("❰ 𝗥 𝗘 𝗪 𝗔 𝗥 𝗗 𝗦 🧧 ❱\n\nClaiming your weekly reward...")
    await asyncio.sleep(2)
    await msg.edit_text("❰ 𝗥 𝗘 𝗪 𝗔 𝗥 𝗗 𝗦 🧧 ❱\n\n◍ **Processing reward...**")
    await asyncio.sleep(2)
    await msg.edit_text(
        "❰ 𝗥 𝗘 𝗪 𝗔 𝗥 𝗗 𝗦 🧧 ❱\n\n"
        "◍ **Weekly reward claimed successfully!**\n"
        "You gained ₩`250,000` 🎉\n\n"
        "Come back next week for more rewards!"
    )

# Assuming `user_collection` and `send_start_button` are already defined
# Dictionary to track user cooldowns
user_last_command_times = {}

@bot.on_message(filters.command("tesure"))
async def daily_reward(_, message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name.strip()
    last_name = message.from_user.last_name.strip() if message.from_user.last_name else ""
    current_time = datetime.utcnow()

    # Check if the user is sending commands too quickly
    if user_id in user_last_command_times and (current_time - user_last_command_times[user_id]).total_seconds() < 5:
        await message.reply_text("You are sending commands too quickly. Please wait for a moment.")
        return
    
    # Update the last command time
    user_last_command_times[user_id] = current_time

    # Debug: Check user's name
    print(f"Debug: User's first name is '{first_name}', last name is '{last_name}'") 

    # Check for specific tags in both first and last name
    if "˹ 𝐃ʏɴᴧϻɪᴄ ˼" not in first_name and "˹ 𝐃ʏɴᴧϻɪᴄ ˼" not in last_name:
        await message.reply_text("Please set `˹ 𝐃ʏɴᴧϻɪᴄ ˼` in your first or last name to use this command.")
        return
    if "𝘿𝙍𝘼𝙂𝙊𝙉𝙎⃟🐉" in first_name or "𝘿𝙍𝘼𝙂𝙊𝙉𝙎⃟🐉" in last_name:
        await message.reply_text("Please remove other tags like `𝘿𝙍𝘼𝙂𝙊𝙉𝙎⃟🐉` and only use `˹ 𝐃ʏɴᴧϻɪᴄ ˼` in your name.")
        return
    
    user_data = await user_collection.find_one({'id': user_id}, projection={'last_tesure_reward': 1, 'balance': 1})
    if not user_data:
        await send_start_button(message.chat.id)
        return

    # Check cooldown time
    last_claimed_time = user_data.get('last_tesure_reward')
    if last_claimed_time:
        last_claimed_time = last_claimed_time.replace(tzinfo=None)
    if last_claimed_time and (current_time - last_claimed_time) < timedelta(minutes=30):
        remaining_time = timedelta(minutes=30) - (current_time - last_claimed_time)
        minutes, seconds = divmod(remaining_time.seconds, 60)
        await message.reply_text(f"Try again in `{minutes}:{seconds}` minutes.")
        return

    # Generate random reward
    reward = random.randint(5000000, 10000000)

    # Button to claim reward
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("💰 Claim Treasure 💰", callback_data=f"claim_tesure_{reward}")]]
    )
    await message.reply_text(
        "❰ 𝗧 𝗥 𝗘 𝗔 𝗦 𝗨 𝗥 𝗘 🧧 ❱\n\n"
        "◍ Click the button below to claim your treasure!\n"
        f"💸 Reward: ₩`{reward:,}`",
        reply_markup=keyboard
    )

@bot.on_callback_query(filters.regex(r"^claim_tesure_(\d+)$"))
async def claim_tesure_reward(_, callback_query):
    user_id = callback_query.from_user.id
    reward = int(callback_query.data.split("_")[-1])
    current_time = datetime.utcnow()

    # Fetch user data
    user_data = await user_collection.find_one({'id': user_id}, projection={'last_tesure_reward': 1, 'balance': 1})
    if not user_data:
        await callback_query.answer("Please start the bot first!", show_alert=True)
        return

    # Check cooldown
    last_claimed_time = user_data.get('last_tesure_reward')
    if last_claimed_time:
        last_claimed_time = last_claimed_time.replace(tzinfo=None)
    if last_claimed_time and (current_time - last_claimed_time) < timedelta(minutes=30):
        remaining_time = timedelta(minutes=30) - (current_time - last_claimed_time)
        minutes, seconds = divmod(remaining_time.seconds, 60)
        await callback_query.answer(f"Try again in {minutes} minutes and {seconds} seconds!", show_alert=True)
        return

    # Update user's balance and last claimed time
    await user_collection.update_one(
        {'id': user_id},
        {'$inc': {'balance': reward}, '$set': {'last_tesure_reward': current_time}}
    )

    # Notify the user
    await callback_query.edit_message_text(
        "❰ 𝗧 𝗥 𝗘 𝗔 𝗦 𝗨 𝗥 𝗘 🧧 ❱\n\n"
        f"◍ Tesure claimed successfully!\n"
        f"You gained ₩`{reward:,}`[.](https://files.catbox.moe/ic7lpw.mp4)",
        disable_web_page_preview=True
)
    
application.add_handler(CommandHandler("tops", mtop, block=False))
application.add_handler(CommandHandler("pay", pay, block=False))

    
async def add_tokens(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    # Check if the user is a sudo user
    if not await is_user_sudo(user_id):
        await update.message.reply_text("🚫 **You don't have permission to add tokens.**")
        return

    # Check if the command includes the required arguments
    if len(context.args) != 2:
        await update.message.reply_text("❌ **Invalid usage.** Usage: `/addt <user_id> <amount>`")
        return

    try:
        target_user_id = int(context.args[0])
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("🚫 **Invalid input. Please provide valid numbers.**")
        return

    # Find the target user
    target_user = await user_collection.find_one({'id': target_user_id})
    if not target_user:
        await update.message.reply_text("🚫 **User not found.**")
        return

    # Update the balance by adding tokens
    new_balance = target_user.get('balance', 0) + amount
    await user_collection.update_one({'id': target_user_id}, {'$set': {'balance': new_balance}})
    await update.message.reply_text(f"✅ **Added** `{amount}` **wealth to user** `{target_user_id}`. \n💰 **New balance:** `{new_balance}` wealth.")

async def delete_tokens(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    # Check if the user is a sudo user
    if not await is_user_sudo(user_id):
        await update.message.reply_text("🚫 **You don't have permission to delete wealth.**")
        return

    # Check if the command includes the required arguments
    if len(context.args) != 2:
        await update.message.reply_text("❌ **Invalid usage.** Usage: `/delt <user_id> <amount>`")
        return

    try:
        target_user_id = int(context.args[0])
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("🚫 **Invalid input. Please provide valid numbers.**")
        return

    # Find the target user
    target_user = await user_collection.find_one({'id': target_user_id})
    if not target_user:
        await update.message.reply_text("🚫 **User not found.**")
        return

    # Check if there are enough tokens to delete
    current_balance = target_user.get('balance', 0)
    if current_balance < amount:
        await update.message.reply_text("❌ **Insufficient wealth to delete.**")
        return

    # Update the balance by deleting tokens
    new_balance = current_balance - amount
    await user_collection.update_one({'id': target_user_id}, {'$set': {'balance': new_balance}})
    await update.message.reply_text(f"✅ **Deleted** `{amount}` **tokens from user** `{target_user_id}`. \n💰 **New balance:** `{new_balance}` tokens.")

async def reset_tokens(update: Update, context: CallbackContext) -> None:
    owner_id = 6402009857  # Replace with the actual owner's user ID
    # Check if the user invoking the command is the owner
    if update.effective_user.id != owner_id:
        await update.message.reply_text("🚫 **You don't have permission to perform this action.**")
        return

    # Reset tokens for all users
    await user_collection.update_many({}, {'$set': {'balance': 10000}})
    
    await update.message.reply_text("🔄 **All user wealth have been reset to** `10,000` **wealth.**")

# Add handlers for the commands
application.add_handler(CommandHandler("addt", add_tokens, block=False))
application.add_handler(CommandHandler("delt", delete_tokens, block=False))
application.add_handler(CommandHandler("reset", reset_tokens, block=False))
