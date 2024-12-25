from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message, InlineQueryResultArticle, InputTextMessageContent, InlineQueryResultPhoto, ReplyKeyboardMarkup, KeyboardButton
from pymongo import ReturnDocument
from shivu import user_collection, collection, CHARA_CHANNEL_ID, SUPPORT_CHAT, shivuu as app, sudo_users, db
from pyrogram.handlers import MessageHandler, CallbackQueryHandler

# Function to get the next sequence number for unique IDs
async def get_next_sequence_number(sequence_name):
    sequence_collection = db.sequences
    sequence_document = await sequence_collection.find_one_and_update(
        {'_id': sequence_name}, 
        {'$inc': {'sequence_value': 1}}, 
        return_document=ReturnDocument.AFTER
    )
    if not sequence_document:
        await sequence_collection.insert_one({'_id': sequence_name, 'sequence_value': 0})
        return 0
    return sequence_document['sequence_value']

# Rarity emojis mapping
rarity_emojis = {
    '🔵 Low': '🔵',
    '🟢 Medium': '🟢',
    '🟣 High': '🟣',
    '🟡 Nobel': '🟡',
    '🥵 Nudes': '🥵',
    '🔮 Limited': '🔮',
    '💋 Cosplay [L]': '💋',
    '⚫️ [X] Verse': '⚫️',
    '❄️ Erotic': '❄️',
    '🍑 Sultry': '🍑'
}

# Dictionary to store the selected anime for each user
user_states = {}


@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    if str(message.from_user.id) in sudo_users:
        sudo_user = await app.get_users(message.from_user.id)
        sudo_user_first_name = sudo_user.first_name
        await message.reply_text(f"ʜᴇʟʟᴏ [{sudo_user_first_name}](tg://user?id={message.from_user.id})!", reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("⚙ Admin panel ⚙")]],
            resize_keyboard=True
        ))


@app.on_message(filters.text & filters.private & filters.regex("^⚙ Admin panel ⚙$"))
async def admin_panel(client, message):
    if str(message.from_user.id) in sudo_users:
        total_waifus = await collection.count_documents({})
        total_animes = await collection.distinct("anime")
        total_harems = await user_collection.count_documents({})
        admin_panel_message = (
            f"ᴀᴅᴍɪɴ ᴘᴀɴᴇʟ:\n\n"
            f"ᴛᴏᴛᴀʟ ᴡᴀɪғᴜs: {total_waifus}\n"
            f"ᴛᴏᴛᴀʟ ᴀɴɪᴍᴇs: {len(total_animes)}\n"
            f"ᴛᴏᴛᴀʟ ʜᴀʀᴇᴍs: {total_harems}"
        )
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🆕 ᴀᴅᴅ ᴡᴀɪғᴜs", callback_data="add_waifu"),
                    InlineKeyboardButton("ᴀᴅᴅ ᴀɴɪᴍᴇ 🆕", callback_data="add_anime")
                ],
                [
                    InlineKeyboardButton("🏖️ ᴀɴɪᴍᴇ ʟɪsᴛ", switch_inline_query_current_chat="choose_anime ")
                ]
            ]
        )
        await app.send_message(message.chat.id, admin_panel_message, reply_markup=keyboard)
    else:
        await message.reply_text("You are not authorized to use this command.")

@app.on_message(filters.command("edit") & filters.private)
async def edit_waifu_command(client, message):
    try:
        if str(message.from_user.id) in sudo_users:
            if len(message.command) < 2:
                await message.reply_text("Please provide the waifu ID. Usage: /edit <waifu_id>")
                return

            waifu_id = message.command[1]
            waifu = await collection.find_one({"id": waifu_id})
            if waifu:
                await message.reply_photo(
                    photo=waifu["img_url"],
                    caption=f"❄️ ɴᴀᴍᴇ: {waifu['name']}\n🎥 ᴀɴɪᴍᴇ: {waifu['anime']}\n🏷 ʀᴀʀɪᴛʏ: {waifu['rarity']}",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [InlineKeyboardButton("🧩 ʀᴇɴᴀᴍᴇ ᴡᴀɪғᴜ", callback_data=f"rename_waifu_{waifu_id}")],
                            [InlineKeyboardButton("⛱️ ᴄʜᴀɴɢᴇ ɪᴍᴀɢᴇ", callback_data=f"change_image_{waifu_id}")],
                            [InlineKeyboardButton("⛩️ ᴄʜᴀɴɢᴇ ʀᴀʀɪᴛʏ", callback_data=f"change_rarity_{waifu_id}")],
                            [InlineKeyboardButton("📢 ʀᴇsᴇᴛ ᴡᴀɪғᴜ", callback_data=f"reset_waifu_{waifu_id}")],
                            [InlineKeyboardButton("🗑️ ʀᴇᴍᴏᴠᴇ ᴡᴀɪғᴜ", callback_data=f"remove_waifu_{waifu_id}")]
                        ]
                    )
                )
            else:
                await message.reply_text("Waifu not found.")
        else:
            await message.reply_text("You are not authorized to use this command.")
    except Exception as e:
        await message.reply_text(f"An error occurred: {str(e)}")

@app.on_callback_query(filters.regex('^add_waifu$'))
async def add_waifu_callback(client, callback_query):
    await callback_query.message.edit_text(
        "Choose an anime to save the waifu in:",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("👾 Search Anime", switch_inline_query_current_chat="choose_anime "),
                    InlineKeyboardButton("⚔️ Cancel", callback_data="cancel_add_waifu")
                ]
            ]
        )
    )
    user_states[callback_query.from_user.id] = {"state": "selecting_anime", "anime": None, "name": None, "rarity": None, "action": "add"}


@app.on_callback_query(filters.regex('^select_rarity_'))
async def select_rarity_callback(client, callback_query):
    selected_rarity = callback_query.data.split('_', 2)[-1]
    user_states[callback_query.from_user.id]["rarity"] = selected_rarity
    user_states[callback_query.from_user.id]["state"] = "awaiting_waifu_image"
    await callback_query.message.edit_text(
        "Now, send the waifu's image:",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("⚔️ Cancel", callback_data="cancel_add_waifu")]]
        )
    )

@app.on_message(filters.private & filters.photo)
async def receive_photo(client, message):
    try:
        user_data = user_states.get(message.from_user.id)

        if user_data:
            if user_data["state"] == "awaiting_waifu_image" and user_data["name"] and user_data["rarity"]:
                # This condition handles adding a new waifu when awaiting the image
                photo_file_id = message.photo.file_id
                id = str(await get_next_sequence_number('character_id')).zfill(2)
                character = {
                    'img_url': photo_file_id,
                    'name': user_data["name"],
                    'anime': user_data["anime"],
                    'rarity': user_data["rarity"],
                    'id': id
                }
                await collection.insert_one(character)
                await message.reply_text("⏳ Adding Character...")
                await app.send_photo(
                    chat_id=CHARA_CHANNEL_ID,
                    photo=photo_file_id,
                    caption=f'➼ <a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}</a> Added New Waifu\nTake a look at this waifu!\n\n</b>{user_data["anime"]}\n</b>{id}: {user_data["name"]}\n(𝙍𝘼𝙍𝙄𝙏𝙔:</b>{user_data["rarity"]})</a>',
                )
                await app.send_photo(
                    chat_id=SUPPORT_CHAT,
                    photo=photo_file_id,
                    caption=f'➼ <a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}</a> Added New Waifu\nTake a look at this waifu!\n\n</b>{user_data["anime"]}\n</b>{id}: {user_data["name"]}\n(𝙍𝘼𝙍𝙄𝙏𝙔:</b>{user_data["rarity"]})</a>',
                )
                await message.reply_text("✅ Character added successfully.")
                user_states.pop(message.from_user.id, None)
            elif user_data["state"] == "changing_image" and user_data["waifu_id"]:
                # This condition handles changing the image of an existing waifu
                waifu_id = user_data["waifu_id"]
                new_image = message.photo.file_id
                waifu = await collection.find_one_and_update(
                    {"id": waifu_id},
                    {"$set": {"img_url": new_image}},
                    return_document=ReturnDocument.AFTER
                )
                if waifu:
                    await message.reply_text("The Character's image has been changed successfully.")
                    await app.send_photo(
                        chat_id=CHARA_CHANNEL_ID,
                        photo=new_image,
                        caption=f"#𝗖𝗛𝗔𝗡𝗚𝗘𝗗𝗣𝗜𝗖\n\n» User: <a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>\n</b>Character Name: '{waifu['name']}'."
                    )
                    await app.send_photo(
                        chat_id=SUPPORT_CHAT,
                        photo=new_image,
                        caption=f"#𝗖𝗛𝗔𝗡𝗚𝗘𝗗𝗣𝗜𝗖\n\n» User: <a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>\n</b>Character Name: '{waifu['name']}'."
                    )
                else:
                    await message.reply_text("Failed to change the waifu's image.")
                user_states.pop(message.from_user.id, None)
    except Exception as e:
        await message.reply_text("An error occurred while processing your request.")
        print(f"Error in receive_photo: {str(e)}")

@app.on_inline_query()
async def search_anime(client, inline_query):
    if str(inline_query.from_user.id) not in sudo_users:
        return

    query = inline_query.query.strip().lower()
    if query.startswith("choose_anime "):
        query = query[len("choose_anime "):]
        anime_results = await collection.aggregate([
            {"$match": {"anime": {"$regex": query, "$options": "i"}}},
            {"$group": {"_id": "$anime", "waifu_count": {"$sum": 1}}},
            {"$limit": 10}
        ]).to_list(length=None)
        
        results = []
        for anime in anime_results:
            title = anime["_id"]
            waifu_count = anime["waifu_count"]
            description = f"Waifus Count: {waifu_count}"
            message_text = f"✏ Title: {title}\n🏷 Characters Count: {waifu_count}"
            
            # Ensure callback data is within the 64-byte limit
            title_encoded = title[:30]  # truncate title to ensure total length < 64 bytes
            inline_buttons = [
                [InlineKeyboardButton("Add Character", callback_data=f"add_waifu_{title_encoded}")],
                [InlineKeyboardButton("Rename Anime", callback_data=f"rename_anime_{title_encoded}")],
                [InlineKeyboardButton("Remove Anime", callback_data=f"remove_anime_{title_encoded}")]
            ]
            reply_markup = InlineKeyboardMarkup(inline_buttons)
            results.append(
                InlineQueryResultArticle(
                    title=title,
                    description=description,
                    input_message_content=InputTextMessageContent(message_text),
                    reply_markup=reply_markup
                )
            )
        
        await inline_query.answer(results, cache_time=1)

@app.on_message(filters.private & filters.text)
async def receive_text_message(client, message):
    user_data = user_states.get(message.from_user.id)
    if user_data:
        if user_data["state"] == "awaiting_waifu_name" and user_data["anime"]:
            # This condition ensures that the function only triggers when adding a new waifu,
            # not when editing an existing one.
            waifu_name = message.text.strip()
            user_states[message.from_user.id]["name"] = waifu_name
            user_states[message.from_user.id]["state"] = "awaiting_waifu_rarity"
            await message.reply_text(
                "Now, choose the waifu's rarity:",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton(rarity, callback_data=f"select_rarity_{rarity}")] 
                        for rarity in rarity_emojis.keys()
                    ]
                )
            )
        elif user_data["state"] == "adding_anime":
            anime_name = message.text.strip()
            existing_anime = await collection.find_one({"anime": anime_name})
            if existing_anime:
                await message.reply_text(f"The anime '{anime_name}' already exists.")
            else:
                anime_document = {"anime": anime_name}
                await collection.insert_one(anime_document)
                await message.reply_text(f"The anime '{anime_name}' has been added successfully.")
            user_states.pop(message.from_user.id, None)
        elif user_data["state"] == "renaming_anime" and user_data["anime"]:
            old_anime_name = user_data["anime"]
            new_anime_name = message.text.strip()
            await collection.update_many({"anime": old_anime_name}, {"$set": {"anime": new_anime_name}})
            await message.reply_text(f"The anime '{old_anime_name}' has been renamed to '{new_anime_name}' successfully.")
            await app.send_message(CHARA_CHANNEL_ID, f"#𝗥𝗘𝗡𝗔𝗠𝗘𝗔𝗡𝗜𝗠𝗘\n\nThe sudo user renamed the anime from '{old_anime_name}' to '{new_anime_name}'.")
            await app.send_message(SUPPORT_CHAT, f"#𝗥𝗘𝗡𝗔𝗠𝗘𝗔𝗡𝗜𝗠𝗘\n\nThe sudo user renamed the anime from '{old_anime_name}' to '{new_anime_name}'.")
            user_states.pop(message.from_user.id, None)
        elif user_data["state"] == "renaming_waifu" and user_data["waifu_id"]:
            # Handling the case of renaming a waifu
            waifu_id = user_data["waifu_id"]
            new_waifu_name = message.text.strip()
            waifu = await collection.find_one({"id": waifu_id})
            if waifu:
                old_name = waifu["name"]
                await collection.update_one(
                    {"id": waifu_id},
                    {"$set": {"name": new_waifu_name}}
                )
                await message.reply_text(f"The waifu has been renamed to '{new_waifu_name}' successfully.")
                await app.send_photo(
                    chat_id=CHARA_CHANNEL_ID,
                    photo=waifu["img_url"],
                    caption=f"#𝗖𝗛𝗔𝗡𝗚𝗘𝗗𝗡𝗔𝗠𝗘\n\n» User: <a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a> Renamed The Character From '{old_name}' To '{new_waifu_name}',"
                )
                await app.send_photo
                    
                await app.send_photo(
                    chat_id=SUPPORT_CHAT,
                    photo=waifu["img_url"],
                    caption=f"#𝗖𝗛𝗔𝗡𝗚𝗘𝗗𝗡𝗔𝗠𝗘\n\n» User: <a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a> Renamed The Character From '{old_name}' To '{new_waifu_name}',"
                )
                await app.send_photo
            else:
                await message.reply_text("Failed to rename the Character.")
            user_states.pop(message.from_user.id, None)

@app.on_callback_query(filters.regex('^add_waifu_'))
async def choose_anime_callback(client, callback_query):
    selected_anime = callback_query.data.split('_', 2)[-1]
    user_states[callback_query.from_user.id] = {"state": "awaiting_waifu_name", "anime": selected_anime, "name": None, "rarity": None}
    await app.send_message(
        chat_id=callback_query.from_user.id,
        text=f"You've selected {selected_anime}. Now, please enter the new Character's name:",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Cancel", callback_data="cancel_add_waifu")]]
        )
    )

@app.on_callback_query(filters.regex('^add_anime$'))
async def add_anime_callback(client, callback_query):
    await callback_query.message.edit_text(
        "Please enter the name of the anime you want to add:"
    )
    user_states[callback_query.from_user.id] = {"state": "adding_anime"}

@app.on_callback_query(filters.regex('^cancel_add_waifu$'))
async def cancel_add_waifu_callback(client, callback_query):
    user_states.pop(callback_query.from_user.id, None)
    await callback_query.message.edit_text("Operation canceled successfully.")

@app.on_callback_query(filters.regex('^rename_anime_'))
async def rename_anime_callback(client, callback_query):
    selected_anime = callback_query.data.split('_', 2)[-1]
    user_states[callback_query.from_user.id] = {"state": "renaming_anime", "anime": selected_anime}

    await app.send_message(
        chat_id=callback_query.from_user.id,
        text=f"You've selected '{selected_anime}'. Please enter the new name for this anime:"
    )

@app.on_callback_query(filters.regex('^remove_anime_'))
async def remove_anime_callback(client, callback_query):
    selected_anime = callback_query.data.split('_', 2)[-1]
    user_states[callback_query.from_user.id] = {"state": "confirming_removal", "anime": selected_anime}

    await app.send_message(
        chat_id=callback_query.from_user.id,
        text=f"Are you sure you want to delete the anime '{selected_anime}'?",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Yes", callback_data="confirm_remove_anime")],
                [InlineKeyboardButton("No", callback_data="cancel_remove_anime")]
            ]
        )
    )
   


@app.on_callback_query(filters.regex('^confirm_remove_anime$'))
async def confirm_remove_anime_callback(client, callback_query):
    user_data = user_states.get(callback_query.from_user.id)
    if user_data and user_data.get("state") == "confirming_removal" and user_data.get("anime"):
        selected_anime = user_data["anime"]
        await collection.delete_many({"anime": selected_anime})
        await callback_query.message.edit_text(f"The anime '{selected_anime}' has been deleted successfully.")
        await app.send_message(CHARA_CHANNEL_ID, f"📢 The sudo user deleted the anime '{selected_anime}'.")
        await app.send_message(SUPPORT_CHAT, f"📢 The sudo user deleted the anime '{selected_anime}'.")
        user_states.pop(callback_query.from_user.id, None)

@app.on_callback_query(filters.regex('^cancel_remove_anime$'))
async def cancel_remove_anime_callback(client, callback_query):
    user_states.pop(callback_query.from_user.id, None)
    await callback_query.message.edit_text("Operation canceled successfully.")


@app.on_callback_query(filters.regex('^rename_waifu_'))
async def rename_waifu_callback(client, callback_query):
    waifu_id = callback_query.data.split('_', 2)[-1]
    user_states[callback_query.from_user.id] = {"state": "renaming_waifu", "waifu_id": waifu_id}
    await callback_query.message.edit_text(
        f"You've selected Character ID: '{waifu_id}'. Please enter the new name for this Character:"
    )


@app.on_callback_query(filters.regex('^change_image_'))
async def change_image_callback(client, callback_query):
    waifu_id = callback_query.data.split('_', 2)[-1]
    user_states[callback_query.from_user.id] = {"state": "changing_image", "waifu_id": waifu_id}
    await callback_query.message.edit_text(
        f"You've selected Character ID: '{waifu_id}'. Please send the new image for this character:",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Cancel", callback_data="cancel_change_image")]]
        )
    )


@app.on_callback_query(filters.regex('^cancel_change_image$'))
async def cancel_change_image_callback(client, callback_query):
    user_states.pop(callback_query.from_user.id, None)
    await callback_query.message.edit_text("Operation canceled successfully.")

@app.on_callback_query(filters.regex('^change_rarity_'))
async def change_rarity_callback(client, callback_query):
    try:
        # Extracting the waifu_id from the callback data
        _, waifu_id = callback_query.data.rsplit('_', 1)

        # Now you have the waifu_id, you can proceed with your logic here
        rarity_keyboard = [
         [InlineKeyboardButton(rarity, callback_data=f"set_rarity_{rarity}_{waifu_id}")]
            for rarity in rarity_emojis.keys()
        ]
        await callback_query.message.edit_text(
            "Choose a new rarity:",
            reply_markup=InlineKeyboardMarkup(rarity_keyboard)
        )
    except Exception as e:
        await callback_query.answer("An error occurred while processing your request.", show_alert=True)
        print(f"Error in change_rarity_callback: {str(e)}")

@app.on_callback_query(filters.regex('^set_rarity_'))
async def set_rarity_callback(client, callback_query):
    try:
        # Extracting the rarity and waifu_id from the callback data
        _, new_rarity, waifu_id = callback_query.data.rsplit('_', 2)

        # Now you have the new_rarity and waifu_id, you can proceed with your logic here
        waifu = await collection.find_one({"id": waifu_id})
        
        if not waifu:
            await callback_query.answer("Waifu not found.", show_alert=True)
            return

        old_rarity = waifu["rarity"]
        await collection.update_one({"id": waifu_id}, {"$set": {"rarity": new_rarity}})
        
        updated_waifu = await collection.find_one({"id": waifu_id})

        # Send update message to the sudo user
        update_message = (
            f"Rarity changed for {updated_waifu['name']}.\n"
            f"Old Rarity: {old_rarity}\n"
            f"New Rarity: {new_rarity}"
        )
        await app.send_photo(callback_query.from_user.id, photo=updated_waifu["img_url"], caption=update_message)

        # Send update message to CHARA_CHANNEL_ID and SUPPORT_CHAT
        await app.send_photo(CHARA_CHANNEL_ID, photo=updated_waifu["img_url"], caption=update_message)
        await app.send_photo(SUPPORT_CHAT, photo=updated_waifu["img_url"], caption=update_message)

        await callback_query.message.edit_text(f"Rarity changed to {new_rarity} successfully.")
    except Exception as e:
        await callback_query.answer("An error occurred while processing your request.", show_alert=True)
        print(f"Error in set_rarity_callback: {str(e)}")

@app.on_callback_query(filters.regex('^reset_waifu_'))
async def reset_waifu_callback(client, callback_query):
    waifu_id = callback_query.data.split('_', 2)[-1]
    user_states[callback_query.from_user.id] = {"state": "confirming_reset", "waifu_id": waifu_id}
    await callback_query.message.edit_text(
        f"Are you sure you want to reset the waifu ID '{waifu_id}' to global grabbed 0?",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Yes", callback_data=f"confirm_reset_waifu_{waifu_id}")],
                [InlineKeyboardButton("No", callback_data="cancel_reset_waifu")]
            ]
        )
    )

@app.on_callback_query(filters.regex('^confirm_reset_waifu_'))
async def confirm_reset_waifu_callback(client, callback_query):
    waifu_id = callback_query.data.split('_', 3)[-1]  # Extract waifu ID
    user_data = user_states.get(callback_query.from_user.id)
    if user_data and user_data.get("state") == "confirming_reset" and user_data.get("waifu_id") == waifu_id:
        waifu = await collection.find_one_and_update(
            {"id": waifu_id},
            {"$set": {"global_grabbed": 0}},
            return_document=ReturnDocument.AFTER
        )
        if waifu:
            # Remove from everyone's harem
            await collection.update_many({}, {"$pull": {"harem": waifu_id}})
            await callback_query.message.edit_text(f"The waifu ID '{waifu_id}' has been reset successfully.")
            await app.send_photo(
                chat_id=CHARA_CHANNEL_ID,
                photo=waifu["img_url"],
                caption=f"📢 <a href='tg://user?id={callback_query.from_user.id}'>{callback_query.from_user.first_name}</a> reset the global grabbed of character '{waifu['name']}' to 0."
            )
        else:
            await callback_query.message.edit_text("Failed to reset the waifu.")
        user_states.pop(callback_query.from_user.id, None)

@app.on_callback_query(filters.regex('^cancel_reset_waifu$'))
async def cancel_reset_waifu_callback(client, callback_query):
    user_states.pop(callback_query.from_user.id, None)
    await callback_query.message.edit_text("Operation canceled successfully.")

@app.on_callback_query(filters.regex('^remove_waifu_'))
async def remove_waifu_callback(client, callback_query):
    waifu_id = callback_query.data.split('_', 2)[-1]
    user_states[callback_query.from_user.id] = {"state": "confirming_waifu_removal", "waifu_id": waifu_id}
    await callback_query.message.edit_text(
        f"Are you sure you want to remove the character ID '{waifu_id}'?",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Yes", callback_data="confirm_remove_waifu")],
                [InlineKeyboardButton("No", callback_data="cancel_remove_waifu")]
            ]
        )
    )

@app.on_callback_query(filters.regex('^confirm_remove_waifu$'))
async def confirm_remove_waifu_callback(client, callback_query):
    user_data = user_states.get(callback_query.from_user.id)
    if user_data and user_data.get("state") == "confirming_waifu_removal" and user_data.get("waifu_id"):
        waifu_id = user_data["waifu_id"]
        waifu = await collection.find_one_and_delete({"id": waifu_id})
        if waifu:
            await callback_query.message.edit_text(f"The Character ID '{waifu_id}' has been removed successfully.")
            await app.send_photo(
                chat_id=CHARA_CHANNEL_ID,
                photo=waifu["img_url"],
                caption=f"📢 The sudo user removed the Character '{waifu['name']}'."
            )
            await app.send_photo(
                chat_id=SUPPORT_CHAT,
                photo=waifu["img_url"],
                caption=f"📢 The sudo user removed the Character '{waifu['name']}'."
            )
        else:
            await callback_query.message.edit_text("Failed to remove the waifu.")
        user_states.pop(callback_query.from_user.id, None)

@app.on_callback_query(filters.regex('^cancel_remove_waifu$'))
async def cancel_remove_waifu_callback(client, callback_query):
    user_states.pop(callback_query.from_user.id, None)
    await callback_query.message.edit_text("Operation canceled successfully.")
         
