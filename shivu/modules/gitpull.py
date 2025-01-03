import os
import subprocess
import sys
from time import sleep
import asyncio

from pyrogram import filters
from shivu import shivuu as app, SPECIALGRADE


@app.on_message(filters.command("gitpull"))
async def git_pull_command(client, message):
    if str(message.from_user.id) not in SPECIALGRADE:
        await message.reply("You are not authorized to use this command.")
        return

    await message.reply("Pulling from the repo... please wait.")

    try:
        # Execute the git pull command with a timeout (to prevent hanging)
        result = subprocess.run(
            ["git", "pull", "https://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@github.com/Itachiuchiha786786/Graping", "main"],
            capture_output=True, text=True, check=True, timeout=60  # 60 seconds timeout
        )

        # Check the output and handle accordingly
        if "Already up to date" in result.stdout:
            return await message.reply("✅ Repo is already up to date.")
        elif result.returncode == 0:
            await message.reply(f"✅ Git pull successful! Updating the bot now...\n\n`{result.stdout}`")
            await restart_bot(message)
        else:
            await message.reply("❌ Git pull failed. Please check the logs.")
            return

    except subprocess.CalledProcessError as e:
        await message.reply(f"❌ Git pull failed with error:\n`{e.stderr}`")
    except subprocess.TimeoutExpired:
        await message.reply("❌ Git pull timed out. Please check your connection and try again.")
    except Exception as e:
        await message.reply(f"❌ Unexpected error occurred: {str(e)}")


# Function to handle restarting the bot
async def restart_bot(message):
    await message.reply("`Restarting the bot...`")

    try:
        # Construct the command to restart the bot in Termux
        args = [sys.executable, "-m", "shivu"]  # Adjust this line to your bot's main file/module
        
        # Create a new process in Termux environment to restart the bot
        subprocess.Popen(args)
        sys.exit()  # Ensure the bot exits cleanly before restarting
    except Exception as e:
        await message.reply(f"❌ Failed to restart the bot. Error: {str(e)}")
        return


# Status check after the bot restart to verify it is running correctly
@app.on_message(filters.command("bot"))
async def status_check_command(client, message):
    if str(message.from_user.id) not in SPECIALGRADE:
        await message.reply("You are not authorized to use this command.")
        return

    await message.reply("✅ Bot is up and running!")
