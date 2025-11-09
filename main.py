#  MIT License (header as-is)

import os
import asyncio
import logging
from logging.handlers import RotatingFileHandler

from config import Config
from pyrogram import Client, idle, filters

# --- Optional: PyroMod (Conversations) ---
try:
    from pyromod import listen  # noqa: F401  (only to enable conversations)
except Exception as e:
    logging.warning("PyroMod load warning: %s", e)

# -------- Logger ----------
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

# -------- filters.edited shim for Pyrogram v2 ----------
# Many old plugins use: ~filters.edited
if not hasattr(filters, "edited"):
    from pyrogram.filters import create as _create_filter  # type: ignore

    def _is_edited(_, __, m):
        # True if message is an EDIT (has edit_date)
        return getattr(m, "edit_date", None) is not None

    filters.edited = _create_filter(_is_edited)  # so ~filters.edited works again

# -------- Auth Users ----------
AUTH_USERS = [int(x) for x in (Config.AUTH_USERS or "").split(",") if x.strip().isdigit()]

# -------- Prefixes (if your plugins import it) ----------
prefixes = ["/", "~", "?", "!"]

# -------- Plugins root ----------
plugins = dict(root="plugins")

# -------- Tiny HTTP server for Render port scan ----------
# If service is "Web Service", Render expects a port to be bound.
# We start a minimal aiohttp server when PORT is present.
async def _start_health_server():
    port = int(os.getenv("PORT", "0") or "0")
    if port <= 0:
        return

    try:
        from aiohttp import web

        async def ok(_):
            return web.Response(text="ok")

        app = web.Application()
        app.router.add_get("/", ok)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        LOGGER.info("Health server running on 0.0.0.0:%s", port)
    except Exception as e:
        LOGGER.warning("Health server failed: %s", e)

# -------- Bot client ----------
bot = Client(
    name="bot-session",               # session name
    bot_token=Config.BOT_TOKEN,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    sleep_threshold=20,
    plugins=plugins,
    workers=50,
)

async def main():
    # Start tiny HTTP server if needed by Render
    await _start_health_server()

    # Start bot
    await bot.start()
    me = await bot.get_me()
    LOGGER.info(f"<--- @{me.username} Started (c) STARKBOT --->")
    await idle()
    await bot.stop()
    LOGGER.info("<--- Bot Stopped --->")

if __name__ == "__main__":
    asyncio.run(main())
