#  MIT License
#  (c) Dan / delivrance & contributors

import os
import asyncio
import logging
from logging.handlers import RotatingFileHandler

from config import Config
from pyrogram import Client, idle, filters

# ---- Optional: pyromod (don't crash if missing) ----
try:
    from pyromod import listen  # noqa: F401  (if you use Conversations)
except Exception:
    listen = None  # Safe fallback; app will still start

# ---- Logging (make LOGGER available before plugins import) ----
LOGGER = logging.getLogger("StarkBot")
logging.basicConfig(
    level=logging.INFO,
    format="%(name)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler("log.txt", maxBytes=5_000_000, backupCount=10),
        logging.StreamHandler(),
    ],
)

# ---- Auth users & prefixes (available at module import time) ----
AUTH_USERS = [int(x) for x in str(Config.AUTH_USERS).split(",") if x.strip()]
prefixes = ["/", "~", "?", "!"]

# ---- Pyrogram v2 compatibility: provide filters.edited shim ----
# Many old plugins use `~filters.edited` or `filters.edited`.
# In v2 this attr isn't present; we emulate it here so you don't have to
# touch every plugin file.
if not hasattr(filters, "edited"):
    def _edited_func(_, __, m):
        # edited messages have edit_date set
        return bool(getattr(m, "edit_date", None))
    filters.edited = filters.create(_edited_func)

# ---- Plugins folder ----
plugins = dict(root="plugins")

# ---- Build Client (exists before .start(), so plugins importing from main work) ----
bot = Client(
    "StarkBot",
    bot_token=Config.BOT_TOKEN,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    sleep_threshold=20,
    plugins=plugins,
    workers=50,
    in_memory=True,  # avoids writing session file on disk (optional)
)

async def main():
    await bot.start()
    me = await bot.get_me()
    LOGGER.info(f"<--- @{me.username} Started (c) STARKBOT --->")
    await idle()
    await bot.stop()
    LOGGER.info("<--- Bot Stopped --->")

if __name__ == "__main__":
    # asyncio.get_event_loop().run_until_complete(main())  # old
    asyncio.run(main())
