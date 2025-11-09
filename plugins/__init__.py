from pyrogram import Client, filters
from pyrogram.types import Message
import os
import sys

# Read AUTH_USERS directly from env to avoid circular import
AUTH_USERS = {
    int(x) for x in os.getenv("AUTH_USERS", "").split(",") if x.strip().isdigit()
}

START_POSTER = "https://telegra.ph/file/cef3ef6ee69126c23bfe3.jpg"

@Client.on_message(filters.command(["start"]))
async def start_msg(client: Client, m: Message):
    await client.send_photo(
        m.chat.id,
        photo=START_POSTER,
        caption=(
            "**Hi i am All in One Extractor Bot**.\n"
            "Press **/pw** for **Physics Wallah**..\n\n"
            "Press **/e1** for **E1 Coaching App**..\n\n"
            "Press **/vidya** for **Vidya Bihar App**..\n\n"
            "Press **/ocean** for **Ocean Gurukul App**..\n\n"
            "Press **/winners** for **The Winners Institute**..\n\n"
            "Press **/rgvikramjeet** for **Rgvikramjeet App**..\n\n"
            "Press **/txt** for  **Ankit With Rojgar,**\n**The Mission Institute,**\n**The Last Exam App**..\n\n"
            "Press **/cp** for **classplus appp**..\n\n"
            "Press **/cw** for **careerwill app**..\n\n"
            "Press **/khan** for **Khan Gs app**..\n\n"
            "Press **/exampur** for ** Exampur app**..\n\n"
            "Press **/samyak** for ** Samayak Ias**..\n\n"
            "Press **/chandra** for ** Chandra app**..\n\n"
            "Press **/mgconcept** for **Mgconcept app**..\n\n"
            "Press **/down** for **For Downloading Url lists**..\n\n"
            "Press **/forward** To **Forward from One channel to others**..\n\n"
            "**𝗕𝗼𝘁 𝗢𝘄𝗻𝗲𝗿 : @BTW_Salaar**"
        ),
    )

# Only allow restart from AUTH_USERS (if none set, no one can run restart)
@Client.on_message(filters.command(["restart"]) & filters.user(list(AUTH_USERS)))
async def restart_handler(client: Client, m: Message):
    await m.reply_text("Restarting...", quote=True)
    os.execl(sys.executable, sys.executable, *sys.argv)

@Client.on_message(filters.command(["log"]) & filters.user(list(AUTH_USERS)))
async def log_msg(client: Client, m: Message):
    try:
        await client.send_document(m.chat.id, "log.txt")
    except Exception as e:
        await m.reply_text(f"Couldn't send log: `{e}`", quote=True)
