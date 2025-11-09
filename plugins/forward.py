# plugins/forward.py
# Code edited By Cryptostark (fixed imports + no filters.edited + no circular import)

import os
import time
from pyrogram import Client, filters
from pyrogram.types import Message
from pyromod import listen  # required for bot.ask / bot.listen
from config import Config

# Parse AUTH_USERS from Config (comma separated string expected)
_raw_auth = os.environ.get("AUTH_USERS", Config.AUTH_USERS) if hasattr(Config, "AUTH_USERS") else os.environ.get("AUTH_USERS", "")
# ensure we support both environment override and Config default
if isinstance(_raw_auth, str):
    AUTH_USERS = [int(x) for x in _raw_auth.split(",") if x.strip() != ""]
elif isinstance(_raw_auth, (list, tuple)):
    AUTH_USERS = [int(x) for x in _raw_auth]
else:
    AUTH_USERS = []

# Prefixes (same default as your main)
prefixes = ["/", "~", "?", "!"]

# Use Client as bot (Pyrogram will inject this when loading plugins)
bot = Client  # type: ignore

@Client.on_message(
    filters.chat(AUTH_USERS) & filters.private &
    filters.incoming & filters.command("forward", prefixes=prefixes)
)
async def forward(client: Client, m: Message):
    """
    Usage (interactive):
    - Owner/admin runs /forward (in private chat with bot)
    - Bot asks to forward a message from target channel (message forwarded from that channel)
    - Bot asks for starting and ending forwarded message (user forwards those messages)
    - Bot copies messages from source to target in the specified range
    """
    try:
        # Ask user to forward any message from target channel
        msg = await client.ask(m.chat.id, "**Forward any message from the Target channel\nBot should be admin at both the Channels**")
        # The forwarded message's forward_from_chat is the target chat
        if not msg.forward_from_chat:
            await m.reply_text("Forwarded message doesn't contain a chat. Make sure you forwarded a message from the target channel.")
            return
        t_chat = msg.forward_from_chat.id

        # Ask for starting message (forward a message from source chat where copying begins)
        msg1 = await client.ask(m.chat.id, "**Send Starting Message From Where you want to Start forwarding**")
        if not msg1.forward_from_chat or not msg1.forward_from_message_id:
            await m.reply_text("Starting message must be a forwarded message (forward a message from source channel).")
            return

        # Ask for ending message (forward a message from source chat where copying ends)
        msg2 = await client.ask(m.chat.id, "**Send Ending Message from same chat**")
        if not msg2.forward_from_chat or not msg2.forward_from_message_id:
            await m.reply_text("Ending message must be a forwarded message (forward a message from source channel).")
            return

        # Validate both forwarded-from chats are same
        if msg1.forward_from_chat.id != msg2.forward_from_chat.id:
            await m.reply_text("Starting and ending forwarded messages must be forwarded from the same source chat.")
            return

        i_chat = msg1.forward_from_chat.id
        s_msg = int(msg1.forward_from_message_id)
        f_msg = int(msg2.forward_from_message_id) + 1

        await m.reply_text('**Forwarding Started**\n\nPress /restart to Stop and /log to get log TXT file')

        # iterate and copy
        for i in range(s_msg, f_msg):
            try:
                await client.copy_message(
                    chat_id=t_chat,
                    from_chat_id=i_chat,
                    message_id=i
                )
            except Exception:
                # continue on errors (message deleted / can't copy)
                continue

        await m.reply_text("Done Forwarding")
    except Exception as e:
        await m.reply_text(f"Error: {e}")
