# LennyC2
Simple C2 framework written in Python. No crazy evasion or wacky and 1337 hacker features. Just basic python, with the ability to run commands and make API calls.

LennyC2 is currently in the "aspirational" phase of it's design and is not yet battle-tested for serious hacking.

## Philosophy
Lenny aims to be unique in that it is only written in scripting languages and is not compiled. Scripts are fundamentally harder to signature than binaries; there is limited metadata (no compile time information, debug metadata... ); brittle signatures like strings can easily be changed (or they can just be randomized from the start), and there is no need to worry about code signing, as e.g. Python.exe and Powershell.exe are always signed, legitimate executables. As a result, heuristic detections and pattern recognitions are generally the best defenses, e.g. signaturing "python.exe executed net.exe as a subprocess, and then made an HTTPS connection." While such heuristic defenses are absolutely possible to implement, they generally require environment-specific tuning, configuration, and monitoring to differentiate them from legitimate script behavior which varies widely across environments. As a result, they are expensive to employ properly. 

## Difficult to deploy?
One of the knocks against script-based C2 frameworks is that they are more difficult to deploy. Sure, it's easy to drop an executable and be on with your day, but executables are also subject to heavier scrutiny (fork/exec syscalls tend to be the most heavily monitored). Also come on guys, we are hackers, let's just get good and work a little harder.

## What if Python isn't installed on my target?
IDK, maybe install it yourself? Sounds like a good use for a stage 0. You could also bring along a valid, signed, statically-linked version of python to do the heavy lifting.

## Wait, I have a better idea. I'll use PyInstaller or Nuitka to compile my python into an unsigned executable that also includes a python bootloader. That will never get caught.
[Please see here for my response](https://www.youtube.com/watch?v=5hfYJsQAhl0)

OK, maybe that's too spicy of a response, but in all seriousness, I would generally recommend against this for actual red team engagements. For the record, I love PyInstaller and often use it in non-pen-testing scenarios. However, PyInstaller-generated binaries often get rolled up in heuristic detections, even if they are signed. And, it goes against the entire philosophy of this C2 framework by bloating a lightweight script with all of the weight of a python executable and bootstrapper. I'm not saying you can't do it, but our loveable mascot, Lenny, will be truly saddened by it.

## Mitigating against malicious scripts
To mitigate a malicious python script, heuristic detection actually needs to be dialed in really well. I am skeptical that many (any?) out-of-the-box EDRs will be tuned well enough to catch a python script that's only real signatureable characteristics are basic file I/O, running commands, and making HTTPS requests to well-known domains. I am not ruling out that it's possible, of course -- just difficult :)

## Disclaimer
LennyC2 is only intended for lawful use. The author is in no way responsible for any illegal use of this software. I am also not responsible for any damages or mishaps that may happen in the course of using this software. Use at your own risk.
