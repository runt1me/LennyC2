# LennyC2
Simple C2 framework written in Python. No crazy evasion or wacky and 1337 hacker features. Just basic python, with the ability to run commands and make API calls.

Currently, all command-and-control is done in Discord. Other [LOTS](https://lots-project.com/) C2 sites may be added in the future. Ping me if you are interested in a particular C2 idea.

Features include:
- Each agent will create its own channel in your Discord server
- Get files from target (will be saved as attachments in your server)
- Put files to target by attaching them to your Discord thread. These will ultimately served by the Discord CDN when they are downloaded.
- Run system commands by prepending `exec`: `exec whoami`
- Basic filesystem traversal, e.g. `pwd`, `cd`, `ls`

## Usage
If needed, run the stager.ps1 script to install python:
`PS > .\stager.ps1`

As LennyC2 is intended to be deployed to (authorized) pen-test/red-team targets, and not our own systems, discord-server related secrets are read from STDIN in an attempt to protect them. The secrets will live in memory in the python process (they must in order for the program to work), but will not be easily visible on process command lines or in logs. First, create a file, `secrets.txt`, with two lines. The DISCORD_USER_ID is the user ID for the account that will be issuing commands to the agent. The DISCORD_BOT_TOKEN is just the normal discord bot token.
```
DISCORD_USER_ID
DISCORD_BOT_TOKEN
```

More information on how to find these values can be found [here](https://infosecwriteups.com/using-discord-as-a-c2-cf90b3480689). Do note that LennyC2 uses the user ID, rather than the server ID, as the linked writeup suggests.

Once the file has been created, you can deploy and run the agent:
`python agent.py < secrets.txt`

You can delete `secrets.txt` once the agent has started.

If everything worked to this point, you should get a callback in a new channel in your Discord server.

## Usage (screenshots)
<img width="1919" height="929" alt="lenny_3" src="https://github.com/user-attachments/assets/699d3fb9-bf17-4ade-9f61-affdf838eb15" />

<img width="962" height="931" alt="lenny_4" src="https://github.com/user-attachments/assets/719ab89f-1ca3-49bb-8ae9-f50182d3edbc" />

<img width="962" height="785" alt="lenny_5" src="https://github.com/user-attachments/assets/da6400f7-bb14-4fb2-b8e1-f73e345477be" />

<img width="961" height="781" alt="lenny_6" src="https://github.com/user-attachments/assets/73943f56-30da-44e5-b605-fc6c6176d3eb" />

<img width="553" height="137" alt="lenny_7" src="https://github.com/user-attachments/assets/0d3e45f6-e257-45a9-8576-ae45ba842f24" />

<img width="617" height="286" alt="lenny_8" src="https://github.com/user-attachments/assets/6b3929dd-cf8e-4f14-b623-c810a678f726" />

## Philosophy
Lenny aims to be unique in that it is only written in scripting languages and is not compiled. Scripts are fundamentally harder to signature than binaries; there is limited metadata (no compile time information, debug metadata... ); brittle signatures like strings can easily be changed (or they can just be randomized from the start), and there is no need to worry about code signing, as e.g. Python.exe and Powershell.exe are always signed, legitimate executables. As a result, heuristic detections and pattern recognitions are generally the best defenses, e.g. signaturing "python.exe executed net.exe as a subprocess, and then made an HTTPS connection." While such heuristic defenses are absolutely possible to implement, they generally require environment-specific tuning, configuration, and monitoring to differentiate them from legitimate script behavior which varies widely across environments. As a result, they are expensive to employ properly. 

## Difficult to deploy?
One of the knocks against script-based C2 frameworks is that they are more difficult to deploy. Sure, it's easy to drop an executable and be on with your day, but executables are also subject to heavier scrutiny (fork/exec syscalls tend to be the most heavily monitored). Also come on guys, we are hackers, let's just get good and work a little harder.

## What if Python isn't installed on my target?
Run the PowerShell script called `stager.ps1` to install Python 3.11.

## This uses third-party python modules that aren't installed on my target.
LennyC2 uses a dynamic importing system for third-party modules. Only python core is needed to bootstrap, and the third-party modules that it needs will be loaded at runtime.

## Wait, I have a better idea. I'll use PyInstaller or Nuitka to compile my python into an unsigned executable that also includes a python bootloader. That will never get caught.
[Please see here for my response](https://www.youtube.com/watch?v=5hfYJsQAhl0)

OK, maybe that's too spicy of a response, but in all seriousness, I would generally recommend against this for actual red team engagements. For the record, I love PyInstaller and often use it in non-pen-testing scenarios. However, PyInstaller-generated binaries often get rolled up in heuristic detections, even if they are signed. And, it goes against the entire philosophy of this C2 framework by bloating a lightweight script with all of the weight of a python executable and bootstrapper. I'm not saying you can't do it, but our loveable mascot, Lenny, will be truly saddened by it.

## Mitigating against malicious scripts
To mitigate a malicious python script, heuristic detection actually needs to be dialed in really well. I am skeptical that many (any?) out-of-the-box EDRs will be tuned well enough to catch a python script that's only real signatureable characteristics are basic file I/O, running commands, and making HTTPS requests to well-known domains. I am not ruling out that it's possible, of course -- just difficult :)

## Where does the name "Lenny" come from?
[My wife, who is currently in law school.](https://www.law.cornell.edu/wex/rule_of_lenity)

## Disclaimer
LennyC2 is only intended for lawful use. The author is in no way responsible for any illegal use of this software. I am also not responsible for any damages or mishaps that may happen in the course of using this software. Use at your own risk.
