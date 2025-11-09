#  MIT License
#  (c) ACE / StarkBot

import os
import asyncio
import logging
from logging.handlers import RotatingFileHandler

from config import Config
from pyrogram import Client, idle, filters

# Optional: if you actually use Conversations
try:
    from pyromod import listen  # noqa: F401
except Exception:
    pass

# ---------------- Logging ----------------
LOGGER = logging.getLogger("StarkBot")
logging.basicConfig(
    level=logging.INFO,
    format="%(name)s - %(message)s",
    handlers=[
        RotatingFileHandler("log.txt", maxBytes=5_000_000, backupCount=10),
        logging.StreamHandler(),
    ],
)

# --------------- Auth / Prefix ---------------
AUTH_USERS = [int(x) for x in (Config.AUTH_USERS or "").split(",") if x.strip().isdigit()]
prefixes = ["/", "~", "?", "!"]

# --------------- Pyrogram v2 compat: filters.edited ---------------
# A lot of old plugins use filters.edited (removed in v2).
# We provide a tiny shim so you DON'T need to edit all plugins.
if not hasattr(filters, "edited"):
    def _edited_func(_, __, m):
        # True if message is an edited message
        return bool(getattr(m, "edit_date", None))
    filters.edited = filters.create(_edited_func)

# --------------- Plugins path ---------------
plugins = dict(root="plugins")

# --------------- Client factory ---------------
def make_client() -> Client:
    """
    IMPORTANT:
    - Use in_memory=True so NO stale user session file is reused.
    - This prevents 401 USER_DEACTIVATED when an old user-session named the
      same as the bot exists. We authenticate ONLY via BOT_TOKEN.
    """
    return Client(
        name="bot-session",
        bot_token=Config.BOT_TOKEN,
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        sleep_threshold=20,
        plugins=plugins,
        workers=50,
        in_memory=True,          # <- KEY FIX for USER_DEACTIVATED
        no_updates=False         # allow handlers
    )

# --------------- Main ---------------
async def main():
    bot = make_client()
    await bot.start()
    me = await bot.get_me()
    LOGGER.info(f"<--- @{me.username} Started (c) STARKBOT --->")
    await idle()
    await bot.stop()
    LOGGER.info("<--- Bot Stopped --->")

if __name__ == "__main__":
    asyncio.run(main())
