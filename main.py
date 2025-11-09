#  MIT License
#  (c) original authors

import os
import asyncio
import logging
from logging.handlers import RotatingFileHandler

from pyrogram import Client, idle, filters
from config import Config

# ---------- Logging ----------
LOGGER = logging.getLogger("starkbot")
logging.basicConfig(
    level=logging.INFO,
    format="%(name)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler("log.txt", maxBytes=5_000_000, backupCount=10),
        logging.StreamHandler(),
    ],
)

# ---------- Env / Config ----------
# AUTH_USERS env -> list[int]
AUTH_USERS = []
if Config.AUTH_USERS:
    try:
        AUTH_USERS = [int(x) for x in str(Config.AUTH_USERS).split(",") if x.strip()]
    except Exception:
        LOGGER.warning("AUTH_USERS env invalid, skipping.")

# ---------- Pyrogram v2 compatibility shim ----------
# A lot of old projects use `~filters.edited`. Pyrogram v2 me `filters.edited` nahi hota.
# To avoid touching every plugin, we monkey-patch a no-op `filters.edited`
if not hasattr(filters, "edited"):
    # create a Filter that always returns False so `~filters.edited` becomes a no-op True filter
    try:
        from pyrogram.filters import create as _create_filter  # v2 helper
        _edited_dummy = _create_filter(lambda *_args, **_kwargs: False, "edited_compat")
    except Exception:
        # Extreme fallback: define minimal object with invert operator
        class _EditedDummy:
            def __invert__(self):  # ~dummy -> truthy object used in & chains
                return self
            def __and__(self, other):  # (~dummy) & X -> X
                return other
            __rand__ = __and__
        _edited_dummy = _EditedDummy()

    # inject into module so plugins can reference `filters.edited`
    setattr(filters, "edited", _edited_dummy)

# ---------- Plugins path ----------
PLUGINS = dict(root="plugins")

# ---------- Build Client ----------
# Important fix for USER_DEACTIVATED:
# Use a fresh in-memory session so old *user* session files don't get reused.
# This ensures bot authenticates purely via BOT_TOKEN.
BOT_SESSION_NAME = "starkbot"
bot = Client(
    name=BOT_SESSION_NAME,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    sleep_threshold=20,
    plugins=PLUGINS,
    workers=50,
    in_memory=True,  # <-- critical: prevents stale user sessions from disk
)

async def main():
    await bot.start()
    me = await bot.get_me()
    LOGGER.info(f"<--- @{me.username} Started (Pyrogram v2) --->")
    await idle()
    await bot.stop()
    LOGGER.info("<--- Bot Stopped --->")

if __name__ == "__main__":
    # Prefer asyncio.run in modern Python
    asyncio.run(main())
