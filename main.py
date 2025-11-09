#  MIT License
#  (c) ACE / StarkBot setup – cleaned for Render

import os
import asyncio
import logging
from logging.handlers import RotatingFileHandler

from pyrogram import Client, idle  # Pyrogram v1.x
from pyromod import listen  # noqa: F401  (if you use Conversations)
import tgcrypto  # noqa: F401

# ---------------- Logging ----------------
LOGGER = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(name)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler("log.txt", maxBytes=5_000_000, backupCount=10),
        logging.StreamHandler(),
    ],
)

# ---------------- Config ----------------
# Prefer env over hardcoded defaults
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
AUTH_USERS_ENV = os.getenv("AUTH_USERS", "")

if not (BOT_TOKEN and API_ID and API_HASH):
    raise RuntimeError("BOT_TOKEN / API_ID / API_HASH are missing in environment")

# Auth Users list
AUTH_USERS = [int(x) for x in AUTH_USERS_ENV.split(",") if x.strip().isdigit()]

# Command prefixes that plugins may import
prefixes = ["/", "~", "?", "!"]

# Plugins root
plugins = dict(root="plugins")

# ---------------- Client ----------------
# in_memory=True => no .session file saved => avoids USER_DEACTIVATED due to stale sessions
# name kept constant for plugin logs
stark = Client(
    name="bot-session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=plugins,
    workers=50,
    sleep_threshold=20,
    in_memory=True,
)

# Also expose alias 'bot' if some plugins import it
bot = stark


async def main():
    await bot.start()
    me = await bot.get_me()
    LOGGER.info(f"<--- @{me.username} Started (c) STARKBOT --->")
    await idle()  # block here until SIGTERM/SIGINT
    await bot.stop()
    LOGGER.info("<--- Bot Stopped --->")


if __name__ == "__main__":
    asyncio.run(main())
