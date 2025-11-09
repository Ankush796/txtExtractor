#  MIT License
#  (c) original authors

import os
import sys
import asyncio
import logging
from logging.handlers import RotatingFileHandler

# --- Make this module importable as "main" for plugins ----
# Plugins often do: from main import LOGGER, prefixes, AUTH_USERS
sys.modules['main'] = sys.modules[__name__]

from pyrogram import Client, idle, filters
try:
    # Optional: only used if you use Conversations; present in requirements
    from pyromod import listen  # noqa: F401
except Exception:
    pass

# ----- Config via env (Render me aap env set kar rahe ho) -----
BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH")
AUTH_USERS = [int(x) for x in os.environ.get("AUTH_USERS", "").split(",") if x.strip().isdigit()]

# ----- Logging -----
LOGGER = logging.getLogger("StarkBot")
LOGGER.setLevel(logging.INFO)
_formatter = logging.Formatter("%(name)s - %(message)s")
_stream = logging.StreamHandler()
_stream.setFormatter(_formatter)
_rot = RotatingFileHandler("log.txt", maxBytes=5_000_000, backupCount=10)
_rot.setFormatter(_formatter)
LOGGER.addHandler(_stream)
LOGGER.addHandler(_rot)

# ----- Command prefixes that plugins import -----
prefixes = ["/", "~", "?", "!"]

# ----- Pyrogram v2 compatibility: filters.edited shim -----
# Some old plugins use ~filters.edited to ignore edited messages.
# In v2, filters.edited may not exist; we recreate it.
if not hasattr(filters, "edited"):
    def _is_edited(_, __, m):
        # True if message has edit_date (i.e., it's an edited message)
        return bool(getattr(m, "edit_date", None))
    filters.edited = filters.create(_is_edited)

# ----- Plugins root -----
plugins = dict(root="plugins")

# ----- Sanity checks -----
if not BOT_TOKEN or not API_ID or not API_HASH:
    raise RuntimeError("Missing BOT_TOKEN / API_ID / API_HASH in environment variables.")

async def main():
    bot = Client(
        "StarkBot",
        bot_token=BOT_TOKEN,
        api_id=API_ID,
        api_hash=API_HASH,
        sleep_threshold=20,
        plugins=plugins,
        workers=50
    )

    await bot.start()
    me = await bot.get_me()
    LOGGER.info(f"<--- @{me.username} Started (c) STARKBOT --->")
    try:
        await idle()
    finally:
        await bot.stop()
        LOGGER.info("<---Bot Stopped--->")

if __name__ == "__main__":
    asyncio.run(main())
