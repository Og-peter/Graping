import time
import asyncio
import random
from pyrogram import filters, Client, types as t
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

# Game constants
zombies = {
    "Normal Zombie": {"health": 100, "damage": 10, "emoji": "🧟", "reward": 5},
    "Fast Zombie": {"health": 150, "damage": 15, "emoji": "⚡🧟", "reward": 10},
    "Tank Zombie": {"health": 300, "damage": 20, "emoji": "🛡️🧟", "reward": 20},
    "Mutated Zombie": {"health": 400, "damage": 25, "emoji": "🧪🧟", "reward": 30},
    "Boss Zombie": {"health": 700, "damage": 50, "emoji": "👑🧟", "reward": 50},
}

guns = {
    "Pistol": {"damage": 20, "reload_time": 2, "emoji": "🔫", "ammo": 15},
    "Shotgun": {"damage": 50, "reload_time": 3, "emoji": "🔥", "ammo": 5},
    "Rifle": {"damage": 30, "reload_time": 1, "emoji": "🔫🔫", "ammo": 20},
    "Sniper": {"damage": 100, "reload_time": 5, "emoji": "🎯", "ammo": 3},
    "Rocket Launcher": {"damage": 200, "reload_time": 8, "emoji": "💥", "ammo": 1},
    "Flamethrower": {"damage": 40, "reload_time": 3, "emoji": "🔥🔥", "ammo": 10, "special": "Burn"},
}

player_data = {}

random_events = [
    {"event": "Healing Pack Found!", "type": "heal", "value": 30, "message": "You healed by 30 HP!"},
    {"event": "Ammo Crate Found!", "type": "ammo", "value": 5, "message": "All guns reloaded with 5 extra ammo!"},
    {"event": "Zombie Mutation!", "type": "mutate", "message": "The zombie has mutated! Its health and damage increased!"},
]

# Helper function to format player stats
def format_stats(player):
    stats = (
        f"**Health:** {player['health']}\n"
        f"**Score:** {player['score']}\n"
        f"**Wave:** {player['zombie_wave']}\n\n"
        "**Ammo:**\n" + "\n".join([f"{guns[gun]['emoji']} {gun}: {player['ammo'][gun]} ammo" for gun in guns])
    )
    return stats

# Command to start the game
@Client.on_message(filters.command(["startgame"]))
async def start_game(_, message: t.Message):
    user_id = message.from_user.id

    # Initialize player data
    player_data[user_id] = {
        "health": 100,
        "ammo": {gun: guns[gun]["ammo"] for gun in guns},
        "zombie_wave": 1,
        "score": 0,
    }

    await message.reply_text(
        "🎮 **Welcome to Advanced Zombie Mode!** 🎮\n\n"
        "Zombies are coming! Prepare your weapons and stay alive.\n\n"
        "Type /zfight to begin the first wave!",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Start Fighting", callback_data="start_fight")]]
        ),
    )

# Function to handle waves
@Client.on_callback_query(filters.regex("start_fight"))
async def start_fight(_, callback_query: t.CallbackQuery):
    user_id = callback_query.from_user.id

    if user_id not in player_data:
        await callback_query.message.reply_text("Start a new game using /startgame.")
        return

    # Spawn a zombie for the wave
    wave = player_data[user_id]["zombie_wave"]
    zombie_type = random.choice(list(zombies.keys()))
    zombie_data = zombies[zombie_type].copy()
    player_data[user_id]["current_zombie"] = zombie_data

    await callback_query.message.reply_photo(
        photo="https://files.catbox.moe/41tiv6.jpg",  # Replace with relevant image URL
        caption=(
            f"**Wave {wave}: {zombie_data['emoji']} {zombie_type}**\n\n"
            f"Zombie Health: {zombie_data['health']}\n"
            f"Zombie Damage: {zombie_data['damage']}\n\n"
            "Choose your gun to attack!"
        ),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(f"{guns[gun]['emoji']} {gun}", callback_data=f"gun_{gun}")
                    for gun in guns.keys()
                ]
            ]
        ),
    )

# Function to handle gun selection and attacks
@Client.on_callback_query(filters.regex(r"gun_(.+)"))
async def attack(_, callback_query: t.CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in player_data or "current_zombie" not in player_data[user_id]:
        await callback_query.message.reply_text("Start a new game using /startgame.")
        return

    gun_name = callback_query.data.split("_")[1]
    if gun_name not in guns:
        await callback_query.message.reply_text("Invalid gun selection.")
        return

    player = player_data[user_id]
    gun = guns[gun_name]
    zombie = player["current_zombie"]

    if player["ammo"][gun_name] <= 0:
        await callback_query.answer("Out of ammo! Reload or choose another gun.", show_alert=True)
        return

    # Attack the zombie
    player["ammo"][gun_name] -= 1
    zombie["health"] -= gun["damage"]

    # Special gun effect
    if gun.get("special") == "Burn":
        zombie["health"] -= 10
        await callback_query.answer("🔥 Burn effect! Extra 10 damage dealt.", show_alert=True)

    if zombie["health"] <= 0:
        # Zombie defeated
        player["score"] += zombie["reward"]
        player["zombie_wave"] += 1

        await callback_query.message.reply_text(
            f"🎉 **Zombie Defeated!** 🎉\n\n"
            f"You earned {zombie['reward']} points.\n"
            f"Total Score: {player['score']}\n\n"
            f"Type /fight to start the next wave!",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Next Wave", callback_data="start_fight")]]
            ),
        )
    else:
        # Zombie still alive, random chance of event
        event_triggered = random.random() < 0.2
        if event_triggered:
            event = random.choice(random_events)
            if event["type"] == "heal":
                player["health"] += event["value"]
                player["health"] = min(player["health"], 100)  # Cap health at 100
            elif event["type"] == "ammo":
                for gun in guns:
                    player["ammo"][gun] += event["value"]
            elif event["type"] == "mutate":
                zombie["health"] += 50
                zombie["damage"] += 5
            await callback_query.message.reply_text(f"**Random Event:** {event['event']} - {event['message']}")

        # Update stats
        await callback_query.message.edit_caption(
            caption=(
                f"**Wave {player['zombie_wave']}: {zombie['emoji']} Zombie**\n\n"
                f"Zombie Health: {zombie['health']}\n"
                f"Player Ammo ({gun_name}): {player['ammo'][gun_name]}\n\n"
                f"Keep fighting or choose another gun!"
            ),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(f"{guns[gun]['emoji']} {gun}", callback_data=f"gun_{gun}")
                        for gun in guns.keys()
                    ]
                ]
            ),
        )

# Additional Commands
@Client.on_message(filters.command(["stats"]))
async def stats(_, message: t.Message):
    user_id = message.from_user.id
    if user_id not in player_data:
        await message.reply_text("Start a new game using /startgame.")
        return

    await message.reply_text(f"🎯 **Player Stats:** 🎯\n\n{format_stats(player_data[user_id])}")

@Client.on_message(filters.command(["reload"]))
async def reload(_, message: t.Message):
    user_id = message.from_user.id
    if user_id not in player_data:
        await message.reply_text("Start a new game using /startgame.")
        return

    for gun in guns:
        player_data[user_id]["ammo"][gun] = guns[gun]["ammo"]

    await message.reply_text("🔄 All guns have been reloaded!")

# Reset command for debugging or restarting
@Client.on_message(filters.command(["resetgame"]))
async def reset_game(_, message: t.Message):
    user_id = message.from_user.id
    if user_id in player_data:
        del player_data[user_id]
    await message.reply_text("🔄 Game has been reset. Type /startgame to play again.")
