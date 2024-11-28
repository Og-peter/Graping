import time
import random
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from shivu import shivuu as bot
from shivu import user_collection

# Configuration
MUST_JOIN = "dynamic_gangs"  # Replace with your channel/group username
AUTHORIZED_USER_ID = 7011990425  # Replace with your Telegram user ID
cooldown_duration = 60  # Cooldown in seconds

# Define the mining materials
mines = {
    "Coal": {
        "price": 1,
        "emoji": "🪨",
        "image_url": "https://files.catbox.moe/sw0nnb.jpg",  # Replace with actual URL
        "aliases": ["coal", "c"],
        "win_chance": 70,
    },
    "Iron": {
        "price": 5,
        "emoji": "🔩",
        "image_url": "https://files.catbox.moe/denh2j.jpg",  # Replace with actual URL
        "aliases": ["iron", "i"],
        "win_chance": 50,
    },
    "Silver": {
        "price": 10,
        "emoji": "🥈",
        "image_url": "https://files.catbox.moe/pz7vmd.jpg",  # Replace with actual URL
        "aliases": ["silver", "s"],
        "win_chance": 30,
    },
    "Gold": {
        "price": 20,
        "emoji": "🥇",
        "image_url": "https://files.catbox.moe/7kgy2k.jpg",  # Replace with actual URL
        "aliases": ["gold", "g"],
        "win_chance": 15,
    },
    "Diamond": {
        "price": 50,
        "emoji": "💎",
        "image_url": "https://files.catbox.moe/9makd3.jpg",  # Replace with actual URL
        "aliases": ["diamond", "d"],
        "win_chance": 5,
    },
}

# Cooldown dictionary
user_last_mine_time = {}


@bot.on_message(filters.command(["mine"]))
async def mine_command(_, message: Message):
    user_id = message.from_user.id
    current_time = time.time()

    # Cooldown check
    if user_id in user_last_mine_time and current_time - user_last_mine_time[user_id] < cooldown_duration:
        remaining_time = cooldown_duration - (current_time - user_last_mine_time[user_id])
        return await message.reply_text(f"⛏️ You're on cooldown! Please wait {int(remaining_time)} seconds before mining again.")

    # Check if the user is in the required group/channel
    try:
        await bot.get_chat_member(MUST_JOIN, user_id)
    except Exception:
        link = f"https://t.me/{MUST_JOIN}"
        return await message.reply_text(
            f"Please join our support group to mine materials. [Join here]({link}).",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join", url=link)]]),
            disable_web_page_preview=True,
        )

    # Mining logic
    mined_material = random.choices(
        list(mines.keys()),
        weights=[mines[gem]["win_chance"] for gem in mines],
        k=1
    )[0]
    material_data = mines[mined_material]
    quantity = random.randint(1, 5)
    price = material_data["price"] * quantity

    # Update user inventory
    user_data = await user_collection.find_one({"id": user_id})
    user_inventory = user_data.get("gems", {}) if user_data else {}
    user_inventory[mined_material] = user_inventory.get(mined_material, 0) + quantity
    await user_collection.update_one({"id": user_id}, {"$set": {"gems": user_inventory}}, upsert=True)

    # Send response
    await message.reply_photo(
        photo=material_data["image_url"],
        caption=f"⛏️ You mined:\n\n"
                f"{material_data['emoji']} <b>{mined_material}</b>\n"
                f"Quantity: <b>{quantity}</b>\n"
                f"Value: <b>{price} tokens</b>",
    )
    user_last_mine_time[user_id] = current_time


@bot.on_message(filters.command(["inventory"]))
async def inventory_command(_, message: Message):
    user_id = message.from_user.id

    # Fetch inventory
    user_data = await user_collection.find_one({"id": user_id})
    inventory = user_data.get("gems", {}) if user_data else {}

    if not inventory:
        return await message.reply_text("⛏️ Your inventory is empty! Start mining with /mine.")

    # Create inventory text
    inventory_text = "<b>⛏️ Your Inventory:</b>\n\n"
    for material, quantity in inventory.items():
        inventory_text += f"{mines[material]['emoji']} <b>{material}</b>: {quantity}\n"

    await message.reply_text(inventory_text)


@bot.on_message(filters.command(["sell"]))
async def sell_command(_, message: Message):
    user_id = message.from_user.id
    command_parts = message.text.split()

    if len(command_parts) != 3:
        return await message.reply_text("Usage: /sell <material> <quantity>")

    material_name = command_parts[1].capitalize()
    quantity_to_sell = int(command_parts[2])

    # Validate material
    material = next(
        (key for key, value in mines.items() if material_name.lower() in [key.lower()] + value["aliases"]),
        None
    )
    if not material:
        return await message.reply_text("Invalid material name. Please check your inventory.")

    # Fetch inventory
    user_data = await user_collection.find_one({"id": user_id})
    inventory = user_data.get("gems", {}) if user_data else {}

    if inventory.get(material, 0) < quantity_to_sell:
        return await message.reply_text("You don't have enough of this material to sell.")

    # Calculate price and update inventory
    total_price = mines[material]["price"] * quantity_to_sell
    inventory[material] -= quantity_to_sell
    if inventory[material] == 0:
        del inventory[material]

    await user_collection.update_one({"id": user_id}, {"$set": {"gems": inventory}, "$inc": {"tokens": total_price}})
    await message.reply_text(f"⛏️ Sold {quantity_to_sell} {mines[material]['emoji']} {material} for {total_price} tokens!")


@bot.on_message(filters.user(AUTHORIZED_USER_ID) & filters.command(["reset_inventory"]))
async def reset_inventory_command(_, message: Message):
    user_id = message.reply_to_message.from_user.id if message.reply_to_message else None

    if user_id:
        await user_collection.update_one({"id": user_id}, {"$unset": {"gems": ""}})
        await message.reply_text(f"⛏️ Inventory reset for user {user_id}.")
    else:
        await message.reply_text("Please reply to the user's message to reset their inventory.")
