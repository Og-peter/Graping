from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from html import escape 
import random
import math
from itertools import groupby
from shivu import collection, user_collection, application
async def harem(update: Update, context: CallbackContext, page=0, edit=False) -> None:
    user_id = update.effective_user.id
    
    # Mapping harem mode to rarity values
    harem_mode_mapping = {
        "low": "🔵 Low",
        "medium": "🟢 Medium",
        "high": "🟣 High",
        "nobel": "🟡 Nobel",
        "nudes": "🥵 Nudes",
        "limited": "🔮 Limited",
        "cosplay": "💋 Cosplay [L]",
        "x_verse": "⚫️ [X] Verse",
        "erotic": "❄️ Exotic",
        "slutry": "🍑 Sultry",
        "default": None
    }
    
    user = await user_collection.find_one({'id': user_id})
    if not user:
        await update.message.reply_text("You need to register first by starting the bot in dm.")
        return
    
    characters = user.get('characters', [])
    fav_character_id = user.get('favorites', [])[0] if 'favorites' in user else None
    fav_character = None
    if fav_character_id:
        for c in characters:
            if isinstance(c, dict) and c.get('id') == fav_character_id:
                fav_character = c
                break
    
    hmode = user.get('smode')
    if hmode == "default" or hmode is None:
        characters = [char for char in characters if isinstance(char, dict)]
        characters = sorted(characters, key=lambda x: (x.get('anime', ''), x.get('id', '')))
        rarity_value = "all"
    else:
        rarity_value = harem_mode_mapping.get(hmode, "Unknown Rarity")
        characters = [char for char in characters if isinstance(char, dict) and char.get('rarity') == rarity_value]
        characters = sorted(characters, key=lambda x: (x.get('anime', ''), x.get('id', '')))
    
    if not characters:
        await update.message.reply_text(f"You don't have any ({rarity_value}) harem. Please change it from /nmode.")
        return
    
    character_counts = {k: len(list(v)) for k, v in groupby(characters, key=lambda x: x['id'])}
    total_pages = math.ceil(len(characters) / 10)
    if page < 0 or page >= total_pages:
        page = 0
    
    harem_message = f"<b>{escape(update.effective_user.first_name)}'s ʜᴀʀᴇᴍ - ᴘᴀɢᴇ {page + 1}/{total_pages}</b>\n"
    
    current_characters = characters[page * 10:(page + 1) * 10]
    current_grouped_characters = {k: list(v) for k, v in groupby(current_characters, key=lambda x: x['anime'])}
    included_characters = set()
    
    for anime, characters in current_grouped_characters.items():
        user_anime_count = len([char for char in user['characters'] if isinstance(char, dict) and char.get('anime') == anime])
        total_anime_count = await collection.count_documents({"anime": anime})
        
        harem_message += f'\n⌬ <b>{anime} 〔{user_anime_count}/{total_anime_count}〕</b>\n'
        harem_message += f'⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋\n'
        
        for character in characters:
            if character['id'] not in included_characters:
                count = character_counts[character['id']]
                formatted_id = f"{int(character['id']):04d}"
                harem_message += f'➥ {formatted_id} | {character["rarity"][0]} | {character["name"]} ×{count}\n'
                included_characters.add(character['id'])
        harem_message += f'⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋\n'
    
    keyboard = [
        [InlineKeyboardButton(f"sᴇᴇ ʜᴀʀᴇᴍ", switch_inline_query_current_chat=f"collection.{user_id}")],
        [InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="ignore")]
    ]
    
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("𝐏𝐞𝐯", callback_data=f"harem:{page - 1}:{user_id}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("𝐍𝐞𝐱𝐭", callback_data=f"harem:{page + 1}:{user_id}"))
        keyboard.append(nav_buttons)
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = update.message or update.callback_query.message

    if fav_character and 'img_url' in fav_character:
        if fav_character['img_url'].endswith(('.mp4', '.gif')):
            if edit:
                await message.edit_caption(caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
            else:
                await message.reply_video(video=fav_character['img_url'], caption=harem_message, parse_mode='HTML', reply_markup=reply_markup)
        else:
            if edit:
                await message.edit_caption(caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
            else:
                await message.reply_photo(photo=fav_character['img_url'], caption=harem_message, parse_mode='HTML', reply_markup=reply_markup)
    else:
        if user['characters']:
            random_character = random.choice(user['characters'])
            if 'img_url' in random_character:
                if random_character['img_url'].endswith(('.mp4', '.gif')):
                    if edit:
                        await message.edit_caption(caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
                    else:
                        await message.reply_video(video=random_character['img_url'], caption=harem_message, parse_mode='HTML', reply_markup=reply_markup)
                else:
                    if edit:
                        await message.edit_caption(caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
                    else:
                        await message.reply_photo(photo=random_character['img_url'], caption=harem_message, parse_mode='HTML', reply_markup=reply_markup)
            else:
                if edit:
                    await message.edit_caption(caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
                else:
                    await message.reply_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
        else:
            if edit:
                await message.edit_caption(caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
            else:
                await message.reply_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
async def harem_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data
    _, page, user_id = data.split(':')
    page = int(page)
    user_id = int(user_id)
    if query.from_user.id != user_id:
        await query.answer("It's Not Your Harem", show_alert=True)
        return
    await query.answer()  # Await the answer coroutine

    await harem(update, context, page, edit=True)

async def set_hmode(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    keyboard = [
        [
            InlineKeyboardButton("ᴅᴇꜰᴀᴜʟᴛ", callback_data="default"),
            InlineKeyboardButton("ʀᴀʀɪᴛʏ", callback_data="rarity"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = await update.message.reply_photo(
        photo="https://files.catbox.moe/eo6dvp.jpg",
        caption="ᴘʟᴇᴀꜱᴇ ᴄʜᴏᴏꜱᴇ ʀᴀʀɪᴛʏ ᴛʜᴀᴛ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ꜱᴇᴛ ᴀꜱ ʜᴀʀᴇᴍ ᴍᴏᴅᴇ :",
        reply_markup=reply_markup,
    )
async def hmode_rarity(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [
            InlineKeyboardButton("⌠🔵⌡", callback_data="low"),
            InlineKeyboardButton("⌠🟢⌡", callback_data="medium"),
            InlineKeyboardButton("⌠🟣⌡", callback_data="high"),
        ],
        [
            InlineKeyboardButton("⌠🟡⌡", callback_data="nobel"),
            InlineKeyboardButton("⌠🥵⌡", callback_data="nudes"),
            InlineKeyboardButton("⌠🔮⌡", callback_data="limited"),
        ],
        [
            InlineKeyboardButton("⌠💋⌡ ", callback_data="cosplay"),
            InlineKeyboardButton("⌠⚫️⌡", callback_data="x_verse"),
            InlineKeyboardButton("⌠❄️⌡ ", callback_data="erotic"),
        ],
        [
            InlineKeyboardButton("⌠🍑⌡", callback_data="slutry"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query = update.callback_query
    await query.edit_message_caption(
        caption="ꜱᴇʟᴇᴄᴛ ᴛʜᴇ ʀᴀʀɪᴛʏ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ꜱᴇᴛ",
        reply_markup=reply_markup,
    )
    await query.answer()
async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    if data == "default":
        await user_collection.update_one({'id': user_id}, {'$set': {'smode': data}})
        await query.answer()
        await query.edit_message_caption(
            caption="ʏᴏᴜ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ꜱᴇᴛ ʏᴏᴜʀ ʜᴀʀᴇᴍ ᴍᴏᴅᴇ ᴀꜱ ᴅᴇꜰᴀᴜʟᴛ"
        )
    elif data == "rarity":
        await hmode_rarity(update, context)
    else:
        await user_collection.update_one({'id': user_id}, {'$set': {'smode': data}})
        await query.answer()
        await query.edit_message_caption(f"ᴘʟᴇᴀꜱᴇ ᴄʜᴏᴏꜱᴇ ʀᴀʀɪᴛʏ ᴛʜᴀᴛ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ꜱᴇᴛ ᴀꜱ ʜᴀʀᴇᴍ ᴍᴏᴅᴇ : {data}")


application.add_handler(CommandHandler(["mywaifus"], harem, block=False))
harem_handler = CallbackQueryHandler(harem_callback, pattern='^harem', block=False)
application.add_handler(harem_handler)
application.add_handler(CommandHandler("nmode", set_hmode))
application.add_handler(CallbackQueryHandler(button, pattern='^default$|^rarity$|^low$|^medium$|^high$|^nudes$|^nobel$|^limited$|^cosplay$|^x_verse$|^erotic$|^slutry$', block=False))
