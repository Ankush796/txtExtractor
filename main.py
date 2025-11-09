#  MIT License
#  (c) Original authors

import os
import asyncio
import logging
from logging.handlers import RotatingFileHandler

from config import Config
from pyrogram import Client, idle
from pyromod import listen  # noqa: F401  # if you use Conversations
import tgcrypto  # noqa: F401  # ensure tgcrypto wheels are present

# ---------- Logging ----------
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

# ---------- Auth Users ----------
AUTH_USERS = [int(x) for x in str(Config.AUTH_USERS).split(",") if x.strip().isdigit()]

# ---------- Pyrogram Plugins ----------
plugins = dict(root="plugins")

# ---------- Prefixes ----------
prefixes = ["/", "~", "?", "!"]

# ---------- Build Client (IN-MEMORY session to avoid old/banned user sessions) ----------
def build_client() -> Client:
    """
    Force an in-memory bot session so that any stale *.session tied to a user account
    is NOT loaded. This prevents 401 USER_DEACTIVATED errors.
    """
    return Client(
        name="starkbot-inmem",              # name is irrelevant when in_memory=True
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        bot_token=Config.BOT_TOKEN,
        sleep_threshold=20,
        workers=50,
        plugins=plugins,
        in_memory=True,                     # <--- key fix
        # takeout=False  # default
    )

async def main():
    bot = build_client()
    await bot.start()
    me = await bot.get_me()
    LOGGER.info(f"<--- @{me.username} Started (c) STARKBOT --->")

    # Safety: ensure bot token really used (prevents accidental user login)
    if not me.is_bot:
        LOGGER.error("This session is not a bot session. Exiting to avoid USER_DEACTIVATED issues.")
        await bot.stop()
        return

    await idle()
    await bot.stop()
    LOGGER.info("<--- Bot Stopped --->")

if __name__ == "__main__":
    # Use modern API; avoids deprecated loop handling
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        LOGGER.info("Shutting down (KeyboardInterrupt)")
