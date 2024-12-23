import importlib
import time
import random
import re
import asyncio
import math
from PIL import Image, ImageFilter
import requests
from io import BytesIO
from html import escape
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters
from shivu import collection, top_global_groups_collection, group_user_totals_collection, user_collection, user_totals_collection, shivuu
from shivu import application, SUPPORT_CHAT, UPDATE_CHAT, OWNER_ID, sudo_users, db, LOGGER
from shivu import set_on_data, set_off_data
from shivu.modules import ALL_MODULES

locks = {}
message_counters = {}
spam_counters = {}
last_characters = {}
sent_characters = {}
first_correct_guesses = {}
message_counts = {}
character_message_links = {}

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("shivu.modules." + module_name)

last_user = {}
warned_users = {}

def escape_markdown(text):
    escape_chars = r'\*_`\\~>#+-=|{}.!'
    return re.sub(r'([%s])' % re.escape(escape_chars), r'\\\1', text)

archived_characters = {}

async def message_counter(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.effective_chat.id)
    user_id = update.effective_user.id

    if chat_id not in locks:
        locks[chat_id] = asyncio.Lock()
    lock = locks[chat_id]

    async with lock:
        chat_frequency = await user_totals_collection.find_one({'chat_id': chat_id})
        if chat_frequency:
            message_frequency = chat_frequency.get('message_frequency', 100)
        else:
            message_frequency = 100

        if chat_id in last_user and last_user[chat_id]['user_id'] == user_id:
            last_user[chat_id]['count'] += 1
            if last_user[chat_id]['count'] >= 10:
                if user_id in warned_users and time.time() - warned_users[user_id] < 600:
                    return
                else:
                    await update.message.reply_text(f"⛔️ Flooding | Spamming\nNow I'm ⚠️ Ignoring {update.effective_user.first_name} Existence For Upcoming 10 Minutes")
                    warned_users[user_id] = time.time()
                    return
        else:
            last_user[chat_id] = {'user_id': user_id, 'count': 1}

        if chat_id in message_counts:
            message_counts[chat_id] += 1
        else:
            message_counts[chat_id] = 1

        if message_counts[chat_id] % message_frequency == 0:
            await send_image(update, context)
            message_counts[chat_id] = 0
    
rarity_active = {
    "🔵 𝙇𝙊𝙒": True,
    "🟢 𝙈𝙀𝘿𝙄𝙐𝙈": True,
    "🟣 𝙃𝙄𝙂𝙃": True,
    "🟡 𝙉𝙊𝘽𝙀𝙇": True,
    "🥵 𝙉𝙐𝘿𝙀𝙎": True,
    "🔮 𝙇𝙄𝙈𝙄𝙏𝙀𝘿": True,
    "💋 𝘾𝙊𝙎𝙋𝙇𝘼𝙔 [𝙇]": True,
    "⚫️ [𝙓] 𝙑𝙚𝙧𝙨𝙚": True,
    "❄️ 𝙀𝙍𝙊𝙏𝙄𝘾": True,
    "🍑 𝙎𝙪𝙡𝙩𝙧𝙮": True
}

# Map numbers to rarity strings
rarity_map = {
   1: "🔵 𝙇𝙊𝙒",
   2: "🟢 𝙈𝙀𝘿𝙄𝙐𝙈",
   3: "🟣 𝙃𝙄𝙂𝙃",
   4: "🟡 𝙉𝙊𝘽𝙀𝙇",
   5: "🥵 𝙉𝙐𝘿𝙀𝙎",
   6: "🔮 𝙇𝙄𝙈𝙄𝙏𝙀𝘿",
   7: "💋 𝘾𝙊𝙎𝙋𝙇𝘼𝙔 [𝙇]",
   8: "⚫️ [𝙓] 𝙑𝙚𝙧𝙨𝙚",
   9: "❄️ 𝙀𝙍𝙊𝙏𝙄𝘾",
   10: "🍑 𝙎𝙪𝙡𝙩𝙧𝙮"
 }

RARITY_WEIGHTS = {
    "🔵 𝙇𝙊𝙒": 13,
    "🟢 𝙈𝙀𝘿𝙄𝙐𝙈": 10,
    "🟣 𝙃𝙄𝙂𝙃": 7,
    "🟡 𝙉𝙊𝘽𝙀𝙇": 2.5,
    "🥵 𝙉𝙐𝘿𝙀𝙎": 4,
    "🔮 𝙇𝙄𝙈𝙄𝙏𝙀𝘿": 0.5,
    "💋 𝘾𝙊𝙎𝙋𝙇𝘼𝙔 [𝙇]": 0.5,
    "⚫️ [𝙓] 𝙑𝙚𝙧𝙨𝙚": 0.1,
    "❄️ 𝙀𝙍𝙊𝙏𝙄𝘾": 0.5,
    "🍑 𝙎𝙪𝙡𝙩𝙧𝙮": 0.1
}
async def send_image(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    message_id = update.message.message_id

    all_characters = list(await collection.find({}).to_list(length=None))

    if chat_id not in sent_characters:
        sent_characters[chat_id] = []

    if len(sent_characters[chat_id]) == len(all_characters):
        sent_characters[chat_id] = []

    if 'available_characters' not in context.user_data:
        context.user_data['available_characters'] = [
            c for c in all_characters 
            if 'id' in c 
            and c['id'] not in sent_characters.get(chat_id, [])
            and c.get('rarity') is not None 
            and c.get('rarity') != '💞 Valentine Special'
        ]

    available_characters = context.user_data['available_characters']

    cumulative_weights = []
    cumulative_weight = 0
    for character in available_characters:
        cumulative_weight += RARITY_WEIGHTS.get(character.get('rarity'), 1)
        cumulative_weights.append(cumulative_weight)

    rand = random.uniform(0, cumulative_weight)
    selected_character = None
    for i, character in enumerate(available_characters):
        if rand <= cumulative_weights[i]:
            selected_character = character
            break

    if not selected_character:
        # If no character is selected, choose randomly from all characters
        selected_character = random.choice(all_characters)

    sent_characters[chat_id].append(selected_character['id'])
    last_characters[chat_id] = selected_character

    if chat_id in first_correct_guesses:
        del first_correct_guesses[chat_id]

    rarity_to_emoji = {
        "🔵 𝙇𝙊𝙒": ("🔵", "𝙇𝙊𝙒"),
        "🟢 𝙈𝙀𝘿𝙄𝙐𝙈": ("🟢", "𝙈𝙀𝘿𝙄𝙐𝙈"),
        "🔴 𝙃𝙄𝙂𝙃": ("🟣", "𝙃𝙄𝙂𝙃"),
        "🟡 𝙉𝙊𝘽𝙀𝙇": ("🟡", "𝙉𝙊𝘽𝙀𝙇"),
        "🥵 𝙉𝙐𝘿𝙀𝙎": ("🥵", "𝙉𝙐𝘿𝙀𝙎"),
        "🔮 𝙇𝙄𝙈𝙄𝙏𝙀𝘿": ("🔮", "𝙇𝙄𝙈𝙄𝙏𝙀𝘿"),
        "💋 𝘾𝙊𝙎𝙋𝙇𝘼𝙔 [𝙇]": ("💋", "𝘾𝙊𝙎𝙋𝙇𝘼𝙔 [𝙇]"),
        "⚫️ [𝙓] 𝙑𝙚𝙧𝙨𝙚": ("⚫️", "[𝙓] 𝙑𝙚𝙧𝙨𝙚"),
        "🎭 𝙀𝙍𝙊𝙏𝙄𝘾": ("❄️", "𝙀𝙍𝙊𝙏𝙄𝘾"),
        "🍑 𝙎𝙪𝙡𝙩𝙧𝙮": ("🍑", "𝙎𝙪𝙡𝙩𝙧𝙮")
    }

    rarity_emoji, rarity_name = rarity_to_emoji.get(selected_character.get('rarity'), ("❓", "Unknown"))

    # Download the image and apply a blur
    response = requests.get(selected_character['img_url'])
    img = Image.open(BytesIO(response.content))
    blurred_img = img.filter(ImageFilter.GaussianBlur(10))
    blurred_buffer = BytesIO()
    blurred_img.save(blurred_buffer, format="JPEG")
    blurred_buffer.seek(0)

    message = await context.bot.send_photo(
        chat_id=chat_id,
        photo=blurred_buffer,
        caption=f"""***{rarity_emoji} ᴡᴀɪғᴜ ʜᴀs ᴊᴜsᴛ sᴘᴀᴡɴᴇᴅ ɪɴ ᴛʜᴇ ᴄʜᴀᴛ!🧃ᴀᴅᴅ ᴛʜɪs ᴄʜᴀʀᴀᴄᴛᴇʀ ᴛᴏ ʏᴏᴜʀ ʜᴀʀᴇᴍ ᴜsɪɴɢ /grap [ɴᴀᴍᴇ]***""",
        parse_mode='Markdown'
    )

    character_message_links[chat_id] = message.message_id
    
async def guess(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    if chat_id not in last_characters:
        return

    if chat_id in first_correct_guesses:
        correct_guess_user = first_correct_guesses[chat_id]  # Get the name of the user who guessed correctly
        user_link = f'<a href="tg://user?id={correct_guess_user.id}">{correct_guess_user.first_name}</a>'  # User link
        await update.message.reply_text(f' ᴛʜɪs ᴡᴀɪғᴜ ɢʀᴀᴘᴘᴇᴅ ʙʏ {user_link}\n🥤 ᴡᴀɪᴛ ғᴏʀ ɴᴇᴡ ᴡᴀɪғᴜ ᴛᴏ sᴘᴀᴡɴ....', parse_mode='HTML')
        return

    guess = ' '.join(context.args).lower() if context.args else ''
    
    if "()" in guess or "&" in guess.lower():
        await update.message.reply_text("𝖲𝗈𝗋𝗋𝗒 ! 𝖡𝗎𝗍 𝗐𝗋𝗂𝗍𝖾 𝗇𝖺𝗆𝖾 𝗐𝗂𝗍𝗁𝗈𝗎𝗍 '&' 𝖳𝗈 𝖼𝗈𝗅𝗅𝖾𝖼𝗍...🍂")
        return

    name_parts = last_characters[chat_id]['name'].lower().split()

    if sorted(name_parts) == sorted(guess.split()) or any(part == guess for part in name_parts):

        first_correct_guesses[chat_id] = update.effective_user  # Store the user who guessed correctly
        
        user = await user_collection.find_one({'id': user_id})
        if user:
            update_fields = {}
            if hasattr(update.effective_user, 'username') and update.effective_user.username != user.get('username'):
                update_fields['username'] = update.effective_user.username
            if update.effective_user.first_name != user.get('first_name'):
                update_fields['first_name'] = update.effective_user.first_name
            if update_fields:
                await user_collection.update_one({'id': user_id}, {'$set': update_fields})
            
            await user_collection.update_one({'id': user_id}, {'$push': {'characters': last_characters[chat_id]}})
      
        elif hasattr(update.effective_user, 'username'):
            await user_collection.insert_one({
                'id': user_id,
                'username': update.effective_user.username,
                'first_name': update.effective_user.first_name,
                'characters': [last_characters[chat_id]],
            })
            
        group_user_total = await group_user_totals_collection.find_one({'user_id': user_id, 'group_id': chat_id})
        if group_user_total:
            update_fields = {}
            if hasattr(update.effective_user, 'username') and update.effective_user.username != group_user_total.get('username'):
                update_fields['username'] = update.effective_user.username
            if update.effective_user.first_name != group_user_total.get('first_name'):
                update_fields['first_name'] = update.effective_user.first_name
            if update_fields:
                await group_user_totals_collection.update_one({'user_id': user_id, 'group_id': chat_id}, {'$set': update_fields})
            
            await group_user_totals_collection.update_one({'user_id': user_id, 'group_id': chat_id}, {'$inc': {'count': 1}})
      
        else:
            await group_user_totals_collection.insert_one({
                'user_id': user_id,
                'group_id': chat_id,
                'username': update.effective_user.username,
                'first_name': update.effective_user.first_name,
                'count': 1,
            })
            
        keyboard = [[InlineKeyboardButton(f"✨ ᴄʜᴀʀᴀᴄᴛᴇʀs ✨", switch_inline_query_current_chat=f"collection.{user_id}")]]
        
        await update.message.reply_text(f'✅ <b><a href="tg://user?id={user_id}">{escape(update.effective_user.first_name)}</a></b> You got a new waifu! \n\n🌸𝗡𝗔𝗠𝗘: <b>{last_characters[chat_id]["name"]}</b> \n❇️𝗔𝗡𝗜𝗠𝗘: <b>{last_characters[chat_id]["anime"]}</b> \n{last_characters[chat_id]["rarity"][0]}𝗥𝗔𝗜𝗥𝗧𝗬: <b>{last_characters[chat_id]["rarity"]}</b>\n\n ᴛʜɪs ᴡᴀɪғᴜ ᴀᴅᴅᴇᴅ ɪɴ ʏᴏᴜʀ ʜᴀʀᴇᴍ.. ᴜsᴇ /harem ᴛᴏ sᴇᴇ ʏᴏᴜʀ ʜᴀʀᴇᴍ ✨', parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        message_link = character_message_links.get(chat_id, "#")
        keyboard = [[InlineKeyboardButton("❄️ ғɪɴᴅ ᴡᴀɪғᴜ ❄️", url=message_link)]]
        await update.message.reply_text('ᴘʟᴇᴀsᴇ ᴡʀɪᴛᴇ ᴄᴏʀʀᴇᴄᴛ ɴᴀᴍᴇ... ❌️!', reply_markup=InlineKeyboardMarkup(keyboard))

def main() -> None:
    """Run bot."""
    
    application.add_handler(CommandHandler(["grap"], guess, block=False))
    application.add_handler(MessageHandler(filters.ALL, message_counter, block=False))
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    shivuu.start()
    LOGGER.info("Bot started")
    main()
