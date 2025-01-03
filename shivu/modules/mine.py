import time
import random
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from shivu import shivuu as bot
from shivu import user_collection

# Configuration
MUST_JOIN = "dynamic_gangs"  # Replace with your channel/group username
AUTHORIZED_USER_ID = 7011990425  # Replace with your Telegram user ID
COOLDOWN_DURATION = 60  # Cooldown in seconds
DEFAULT_ENERGY = 100  # Default energy for users
ENERGY_RECHARGE_RATE = 10  # Energy recharged per hour
LEVEL_UP_THRESHOLD = 100  # Points required for each level up

# Define the mining materials
mines = {
    "Coal": {
        "price": 1,
        "emoji": "🪨",
        "image_url": "https://files.catbox.moe/sw0nnb.jpg",
        "win_chance": 70,
        "exp": 5,
    },
    "Iron": {
        "price": 5,
        "emoji": "🔩",
        "image_url": "https://files.catbox.moe/denh2j.jpg",
        "win_chance": 50,
        "exp": 10,
    },
    "Silver": {
        "price": 10,
        "emoji": "🥈",
        "image_url": "https://files.catbox.moe/pz7vmd.jpg",
        "win_chance": 30,
        "exp": 20,
    },
    "Gold": {
        "price": 20,
        "emoji": "🥇",
        "image_url": "https://files.catbox.moe/7kgy2k.jpg",
        "win_chance": 15,
        "exp": 50,
    },
    "Diamond": {
        "price": 50,
        "emoji": "💎",
        "image_url": "https://files.catbox.moe/9makd3.jpg",
        "win_chance": 5,
        "exp": 100,
    },
}

# Cooldown dictionary
user_last_mine_time = {}


def calculate_level(exp):
    """Calculate the user's level based on experience points."""
    return exp // LEVEL_UP_THRESHOLD + 1


async def ensure_user_data(user_id):
    """Ensure the user has a document in the database."""
    user_data = await user_collection.find_one({"id": user_id})
    if not user_data:
        user_data = {
            "id": user_id,
            "exp": 0,
            "energy": DEFAULT_ENERGY,
            "gems": {},
            "tokens": 0,
            "tools": [],
        }
        await user_collection.insert_one(user_data)
    return user_data


@bot.on_message(filters.command(["mine"]))
async def mine_command(_, message: Message):
    user_id = message.from_user.id
    current_time = time.time()

    # Cooldown check
    last_mine_time = user_last_mine_time.get(user_id, 0)
    if current_time - last_mine_time < COOLDOWN_DURATION:
        remaining_time = int(COOLDOWN_DURATION - (current_time - last_mine_time))
        return await message.reply_text(
            f"⛏️ You're on cooldown! Please wait {remaining_time} seconds before mining again."
        )

    # Ensure the user is in the required group
    try:
        await bot.get_chat_member(MUST_JOIN, user_id)
    except Exception:
        link = f"https://t.me/{MUST_JOIN}"
        return await message.reply_text(
            f"Please join our group to mine materials. [Join here]({link}).",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join", url=link)]]),
            disable_web_page_preview=True,
        )

    # Fetch or initialize user data
    user_data = await ensure_user_data(user_id)

    # Ensure the 'energy' key exists
    if "energy" not in user_data:
        user_data["energy"] = DEFAULT_ENERGY
        await user_collection.update_one({"id": user_id}, {"$set": {"energy": DEFAULT_ENERGY}})

    # Check energy
    if user_data["energy"] <= 0:
        return await message.reply_text("⛏️ You're out of energy! Wait for it to recharge or use an energy potion.")

    # Mining logic
    mined_material = random.choices(
        list(mines.keys()),
        weights=[mines[gem]["win_chance"] for gem in mines],
        k=1,
    )[0]
    material_data = mines[mined_material]
    quantity = random.randint(1, 5)
    price = material_data["price"] * quantity
    exp_gained = material_data["exp"] * quantity

    # Update inventory and stats
    user_data["energy"] -= 10
    user_data["exp"] += exp_gained
    user_data["gems"][mined_material] = user_data["gems"].get(mined_material, 0) + quantity
    await user_collection.update_one({"id": user_id}, {"$set": user_data}, upsert=True)

    # Send response with image
    await message.reply_photo(
        photo=material_data["image_url"],
        caption=(
            f"⛏️ You mined:\n\n"
            f"{material_data['emoji']} <b>{mined_material}</b>\n"
            f"Quantity: <b>{quantity}</b>\n"
            f"Value: <b>{price} tokens</b>\n"
            f"EXP Gained: <b>{exp_gained}</b>\n"
            f"Your Level: <b>{calculate_level(user_data['exp'])}</b>\n"
            f"Remaining Energy: <b>{user_data['energy']}</b>"
        ),
    )
    user_last_mine_time[user_id] = current_time


@bot.on_message(filters.command(["inventory"]))
async def inventory_command(_, message: Message):
    user_id = message.from_user.id

    # Fetch inventory
    user_data = await ensure_user_data(user_id)
    if not user_data.get("gems"):
        return await message.reply_text("⛏️ Your inventory is empty! Start mining with /mine.")

    # Display inventory
    inventory_text = "<b>⛏️ Your Inventory:</b>\n\n"
    for material, quantity in user_data["gems"].items():
        inventory_text += f"{mines[material]['emoji']} <b>{material}</b>: {quantity}\n"
    inventory_text += (
        f"\n<b>Total Tokens:</b> {user_data.get('tokens', 0)}\n"
        f"<b>Your Level:</b> {calculate_level(user_data['exp'])}\n"
        f"<b>Energy:</b> {user_data['energy']}"
    )

    await message.reply_text(inventory_text)


@bot.on_message(filters.command(["sell"]))
async def sell_command(_, message: Message):
    user_id = message.from_user.id
    command_parts = message.text.split(maxsplit=2)

    if len(command_parts) != 3:
        return await message.reply_text("Usage: /sell <material> <quantity>")

    material_name = command_parts[1].capitalize()
    try:
        quantity_to_sell = int(command_parts[2])
    except ValueError:
        return await message.reply_text("Invalid quantity. Please provide a valid number.")

    # Validate material
    material = mines.get(material_name)
    if not material:
        return await message.reply_text("Invalid material name. Please check your inventory.")

    # Fetch inventory
    user_data = await ensure_user_data(user_id)
    inventory = user_data.get("gems", {})

    if inventory.get(material_name, 0) < quantity_to_sell:
        return await message.reply_text("You don't have enough of this material to sell.")

    # Calculate price and update inventory
    total_price = material["price"] * quantity_to_sell
    inventory[material_name] -= quantity_to_sell
    if inventory[material_name] == 0:
        del inventory[material_name]

    user_data["tokens"] += total_price
    await user_collection.update_one({"id": user_id}, {"$set": {"gems": inventory, "tokens": user_data["tokens"]}})
    await message.reply_text(
        f"⛏️ Sold {quantity_to_sell} {material['emoji']} {material_name} for {total_price} tokens!"
    )
