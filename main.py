#  MIT License
# (c) You

import os
import sys
import asyncio
import logging
from logging.handlers import RotatingFileHandler

from pyrogram import Client, filters, idle

# ---- Optional: pyromod safe import (no crash if unused) ----
try:
    from pyromod import listen  # noqa: F401
except Exception:
    pass

# ---- Make this module importable as "main" for old plugins ----
# (plugins that do: from main import LOGGER, prefixes, AUTH_USERS)
sys.modules.setdefault("main", sys.modules[__name__])

# ---- Logger ----
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

# ---- Config via env (fallbacks allowed, but prefer setting env on Render) ----
BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = int(os.environ.get("API_ID", "0") or "0")
API_HASH = os.environ.get("API_HASH")
AUTH_USERS = [
    int(x) for x in os.environ.get("AUTH_USERS", "").split(",") if x.strip().isdigit()
]

# ---- Prefixes (for plugins importing from main) ----
prefixes = ["/", "~", "?", "!"]

# ---- Pyrogram v2 compatibility: add filters.edited if missing ----
if not hasattr(filters, "edited"):
    def _edited(_, __, m):
        # True if message is an edit (has edit_date)
        return bool(getattr(m, "edit_date", None))
    filters.edited = filters.create(_edited)

# ---- Plugins root ----
plugins = dict(root="plugins")


def validate_config():
    missing = []
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not API_ID:
        missing.append("API_ID")
    if not API_HASH:
        missing.append("API_HASH")
    if missing:
        raise RuntimeError(f"Missing required environment vars: {', '.join(missing)}")


async def main():
    validate_config()

    # Client session name keep stable for Render restarts
    app = Client(
        name="bot-session",
        bot_token=BOT_TOKEN,
        api_id=API_ID,
        api_hash=API_HASH,
        sleep_threshold=20,
        plugins=plugins,
        workers=50,
        in_memory=True,  # avoid writing session file to disk
    )

    await app.start()
    me = await app.get_me()
    LOGGER.info(f"<--- @{me.username} Started (c) STARKBOT --->")
    try:
        await idle()
    finally:
        await app.stop()
        LOGGER.info("<--- Bot Stopped --->")


if __name__ == "__main__":
    asyncio.run(main())
