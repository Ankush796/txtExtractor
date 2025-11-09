#  MIT License
#  (c) Your project

import os
import asyncio
import logging
from logging.handlers import RotatingFileHandler

from config import Config
from pyrogram import Client, idle, filters
from pyromod import listen  # conversations helper (installed now)
import tgcrypto  # noqa: F401 (forces wheel load)

# -------------------------------
# Logging
# -------------------------------
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

# -------------------------------
# Global settings for plugins
# (Plugins import these from main)
# -------------------------------
AUTH_USERS = [int(x) for x in str(Config.AUTH_USERS).split(",") if x.strip()]
prefixes = ["/", "~", "?", "!"]  # plugins use this

# -------------------------------
# Pyrogram v1 -> v2 compatibility:
# A lot of old code uses ~filters.edited
# Pyrogram v2 has no filters.edited. We add a shim so that
# "~filters.edited" is always True (i.e., "not edited") without
# touching every plugin.
# -------------------------------
if not hasattr(filters, "edited"):
    # create a filter that never matches; its negation matches all
    # so "~filters.edited" will behave like "not edited" but effectively pass-through
    from pyrogram.filters import create

    filters.edited = create(lambda *_: False)

# -------------------------------
# Small HTTP keep-alive for Render Web Service
# If your Render service type is "Background Worker", you can skip this.
# For Web Service, Render scans $PORT; we open a tiny server to answer "ok".
# -------------------------------
def _start_keepalive_server():
    port = os.environ.get("PORT")
    if not port:
        return
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class _H(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")

        def log_message(self, fmt, *args):
            return  # silence

    def _serve():
        try:
            HTTPServer(("0.0.0.0", int(port)), _H).serve_forever()
        except Exception as e:
            LOGGER.warning(f"Keepalive server error: {e}")

    threading.Thread(target=_serve, daemon=True).start()
    LOGGER.info(f"Keepalive HTTP server listening on :{port}")

# -------------------------------
# Pyrogram Client (bot)
# Key choices:
# - session_name is "bot-session" and in_memory=True to avoid
#   reusing any old *user* session that could trigger USER_DEACTIVATED.
# - plugins auto-load from ./plugins
# -------------------------------
plugins = dict(root="plugins")

bot = Client(
    name="bot-session",
    bot_token=Config.BOT_TOKEN,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    sleep_threshold=20,
    plugins=plugins,
    workers=50,
    in_memory=True,  # critical: prevent stale on-disk sessions
)

async def main():
    _start_keepalive_server()

    await bot.start()
    me = await bot.get_me()
    LOGGER.info(f"<--- @{me.username} Started (c) STARKBOT --->")
    await idle()
    await bot.stop()
    LOGGER.info("<--- Bot Stopped --->")

if __name__ == "__main__":
    asyncio.run(main())
