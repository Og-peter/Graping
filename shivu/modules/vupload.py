import urllib.request
from pymongo import ReturnDocument
from telegram import Update, InlineQueryResultVideo
from telegram.ext import CommandHandler, CallbackContext
from shivu import application, sudo_users, collection, db, CHARA_CHANNEL_ID, SUPPORT_CHAT

WRONG_FORMAT_TEXT_VIDEO = """Wrong ❌ format... eg. /up Video_url character-name anime-name rarity-number"""

CATEGORY_MAP = {
    # Tambahkan kategori lainnya jika diperlukan
    '❄️': '❄️𝑰𝒏𝒇𝒊𝒏𝒊𝒕𝒚❄️',
    # ...
}

def get_category(name):
    for emoji in CATEGORY_MAP:
        if emoji in name:
            return CATEGORY_MAP[emoji]
    return ""

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

async def upload_video(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in sudo_users:
        await update.message.reply_text('Ask My Owner...')
        return

    try:
        args = context.args
        if len(args) != 4:
            await update.message.reply_text(WRONG_FORMAT_TEXT_VIDEO)
            return

        character_name = args[1].replace('-', ' ').title()
        anime = args[2].replace('-', ' ').title()

        try:
            urllib.request.urlopen(args[0])
        except:
            await update.message.reply_text('Invalid URL.')
            return

        rarity_map = {1: "⚜️ Animated"}
        try:
            rarity = rarity_map[int(args[3])]
        except KeyError:
            await update.message.reply_text('Invalid rarity. Please use 1, 2, 3, 4, 5, 6')
            return

        id = str(await get_next_sequence_number('character_id')).zfill(2)
        category = get_category(character_name)

        character = {
            'img_url': args[0],  # Gunakan kunci img_url untuk video/gif juga
            'name': character_name,
            'anime': anime,
            'rarity': rarity,
            'id': id,
            'category': category
        }

        caption = f"Oni chan New Character Added!\n\n{anime}\n{id}: {character_name}\n(𝙍𝘼𝙍𝙄𝙏𝙔: {rarity})\n"
        if category:
            caption += f"\n{category}\n"
        caption += f"\n➼ ᴀᴅᴅᴇᴅ ʙʏ: <a href=\"tg://user?id={update.effective_user.id}\">{update.effective_user.first_name}</a>"

        try:
            # Send video to the character channel
            message = await context.bot.send_video(
                chat_id=CHARA_CHANNEL_ID,
                video=args[0],
                caption=caption,
                parse_mode='HTML'
            )
            character['message_id'] = message.message_id
            await collection.insert_one(character)
            await update.message.reply_text('CHARACTER ADDED....')
        except:
            await collection.insert_one(character)
            await update.message.reply_text("Character Added but no Database Channel Found, Consider adding one.")
        
        # Send the caption message to the support chat
        await context.bot.send_message(
            chat_id=SUPPORT_CHAT,
            text=caption,
            parse_mode='HTML'
        )

    except Exception as e:
        await update.message.reply_text(f'Character Upload Unsuccessful. Error: {str(e)}\nIf you think this is a source error, forward to: {SUPPORT_CHAT}')
        
# Tambahkan handler baru untuk command /up
application.add_handler(CommandHandler('hvupload', upload_video))
