#  MIT License
#  (c) ACE / StarkBot

import os
import asyncio
import logging
from logging.handlers import RotatingFileHandler

from pyrogram import Client, idle
from pyromod import listen  # if you use Conversations
import tgcrypto  # noqa: F401  (ensures TgCrypto wheels are loaded)

# ---------------- Logging ----------------
LOGGER = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(name)s - %(message)s",
    handlers=[
        RotatingFileHandler("log.txt", maxBytes=5_000_000, backupCount=10),
        logging.StreamHandler(),
    ],
)

# ---------------- Config ----------------
# Prefer environment over hardcoded defaults
BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
AUTH_USERS = os.environ.get("AUTH_USERS", "")

# Validate required envs early (better error message)
missing = [k for k, v in [("BOT_TOKEN", BOT_TOKEN), ("API_ID", API_ID), ("API_HASH", API_HASH)] if not v]
if missing:
    raise RuntimeError(f"Missing required env vars: {', '.join(missing)}")

API_ID = int(API_ID)
AUTH_USERS_LIST = [int(x) for x in AUTH_USERS.split(",") if x.strip()]

# Prefixes (some plugins import these from main)
prefixes = ["/", "~", "?", "!"]

plugins = dict(root="plugins")

# --------------- Tiny HTTP server (Render Web Service health) ---------------
# If you run as Web Service on Render, it requires an open port.
# This server is lightweight and won't affect the bot.
async def start_health_server():
    try:
        from aiohttp import web
    except Exception:
        LOGGER.info("aiohttp not installed; skipping health server")
        return

    async def ok(_request):
        return web.Response(text="ok")

    app = web.Application()
    app.add_routes([web.get("/", ok), web.get("/health", ok)])

    port = int(os.environ.get("PORT", "8080"))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    LOGGER.info(f"Health server listening on 0.0.0.0:{port}")

# ---------------- Main ----------------
bot = Client(
    "bot-session",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH,
    sleep_threshold=20,
    plugins=plugins,
    workers=50,
)

async def main():
    # Start health server (harmless if running as Background Worker too)
    health = asyncio.create_task(start_health_server())

    await bot.start()
    me = await bot.get_me()
    LOGGER.info(f"<--- @{me.username} Started (c) STARKBOT --->")
    await idle()

    await bot.stop()
    await health

if __name__ == "__main__":
    asyncio.run(main())
    LOGGER.info("<--- Bot Stopped --->")
