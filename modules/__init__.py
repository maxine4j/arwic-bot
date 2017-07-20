import asyncio
import os
import re
import importlib



for s in os.listdir(__name__):
    m = re.search(r"^(.+)\.py$", s)
    if m is not None:
        g = m.group(1)
        if g.startswith("_"):
            continue
        importlib.import_module("modules." + m.group(1))
        print("Loaded module:", m.group(1))

# enable modules here
modules = [
    music.MusicModule(),
    permissions.PermissionsModule(),
    meme.MemeModule(),
    warcraft.WarcraftModule(),
    admin.AdminModule(),
    embed.EmbedModule()
]

async def try_run_command(prefix, client, message):
    for m in modules:
        if await m.try_run_command(prefix, client, message):
            return True
