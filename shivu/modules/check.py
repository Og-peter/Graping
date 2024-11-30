import urllib.request
import os
from pymongo import ReturnDocument
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from shivu import application, sudo_users, collection, db, CHARA_CHANNEL_ID, user_collection
from shivu import shivuu as bot
from pyrogram import Client, filters, types as t

async def check_character(update: Update, context: CallbackContext) -> None:
    try:
        args = context.args
        if len(args) != 1:
            await update.message.reply_text('Incorrect format. Please use: /check waifu_id')
            return
        character_id = args[0]
        character = await collection.find_one({'id': character_id})
        if character:
            global_count = await user_collection.count_documents({'characters.id': character['id']})
            response_message = (
                f"<b>OwO! Check out this waifu !!</b>\n\n"
                f"{character['id']}: <b>{character['name']}</b>\n"
                f"<b>{character['anime']}</b>\n"
                f"(𝙍𝘼𝙍𝙄𝙏𝙔: {character['rarity']})"
            )
            if '🐰' in character['name']:
                response_message += "\n\n🐰 𝓑𝓾𝓷𝓷𝔂 🐰\n"
            elif '👩‍🏫' in character['name']:
                response_message += "\n\n👩‍🏫 𝓣𝓮𝓪𝓬𝓱𝓮𝓻 👩‍🏫\n"
            elif '🎒' in character['name']:
                response_message += "\n\n🎒 𝓢𝓬𝓱𝓸𝓸𝓵 🎒\n"
            elif '👘' in character['name']:
                response_message += "\n\n👘 𝓚𝓲𝓶𝓸𝓷𝓸 👘\n"
            elif '🏖' in character['name']:
                response_message += "\n\n🏖 𝓢𝓤𝓜𝓜𝓔𝓡 🏖\n"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Globally Grapped", callback_data=f"slaves_{character['id']}_{global_count}")]
            ])

            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=character['img_url'],
                caption=response_message,
                parse_mode='HTML',
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text('Wrong id.')

    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')
        
async def handle_callback_query(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data.split('_')
    if data[0] == 'slaves':
        character_id = data[1]
        global_count = data[2]
        await query.answer(f"⚡️ Globally Grapped : {global_count}x.", show_alert=True)

CHECK_HANDLER = CommandHandler('check', check_character, block=False)
application.add_handler(CallbackQueryHandler(handle_callback_query, pattern='slaves_', block=False))
application.add_handler(CHECK_HANDLER)
