#  MIT License
#  (c) original authors

import os
import asyncio
import logging
from logging.handlers import RotatingFileHandler

from pyrogram import Client, idle
from config import Config

# --- Optional: Conversations via pyromod (won't crash if missing)
try:
    from pyromod import listen  # noqa: F401
    HAVE_PYROMOD = True
except Exception:
    HAVE_PYROMOD = False

# Logging
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

# --- Validate envs early
missing = []
if not os.environ.get("BOT_TOKEN", Config.BOT_TOKEN):
    missing.append("BOT_TOKEN")
if not os.environ.get("API_ID") and not Config.API_ID:
    missing.append("API_ID")
if not os.environ.get("API_HASH", Config.API_HASH):
    missing.append("API_HASH")
if missing:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

# Auth users
AUTH_USERS = []
raw_auth = os.environ.get("AUTH_USERS", getattr(Config, "AUTH_USERS", ""))
if raw_auth:
    for chat in raw_auth.split(","):
        chat = chat.strip()
        if chat.isdigit():
            AUTH_USERS.append(int(chat))

# Command prefixes
prefixes = ["/", "~", "?", "!"]

# Plugins
plugins = dict(root="plugins")

# --- Critical fix:
# Use IN-MEMORY session so Pyrogram never reuses any old user session file.
# This avoids the 401 USER_DEACTIVATED caused by a stale user auth session.
bot = Client(
    name="starkbot",                 # just an identifier (not a file)
    bot_token=os.environ.get("BOT_TOKEN", Config.BOT_TOKEN),
    api_id=int(os.environ.get("API_ID", Config.API_ID)),
    api_hash=os.environ.get("API_HASH", Config.API_HASH),
    sleep_threshold=20,
    plugins=plugins,
    workers=50,
    in_memory=True,                  # <-- no .session file on disk
)

async def main():
    # safety: if any *.session got baked in repo/run dir, remove them
    for f in os.listdir("."):
        if f.endswith(".session") or ".session-journal" in f:
            try:
                os.remove(f)
                LOGGER.info(f"Removed stray session file: {f}")
            except Exception:
                pass

    await bot.start()
    me = await bot.get_me()
    LOGGER.info(f"<--- @{me.username} Started (Pyrogram {bot.__version__}) --->")
    if not HAVE_PYROMOD:
        LOGGER.info("pyromod not installed; Conversations disabled (optional).")
    await idle()
    await bot.stop()
    LOGGER.info("<--- Bot Stopped --->")

if __name__ == "__main__":
    # Modern, safer loop runner
    asyncio.run(main())
