import urllib
import urllib.parse
import requests
import json
import subprocess
from pyrogram.types.messages_and_media import message
import helper
from pyromod import listen
from pyrogram.types import Message
import tgcrypto
import pyrogram
from pyrogram import Client, filters
from pyrogram.types.messages_and_media import message
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import FloodWait
import time
from pyrogram.types import User, Message
from p_bar import progress_bar
from subprocess import getstatusoutput
import logging
import os
import sys
import re
from pyrogram import Client as bot
import cloudscraper
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base64 import b64encode, b64decode

def decode(tn: str) -> str:
    key = "638udh3829162018".encode("utf8")
    iv = "fedcba9876543210".encode("utf8")
    ciphertext = bytearray.fromhex(b64decode(tn.encode()).hex())
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
    url = plaintext.decode('utf-8')
    return url

# NOTE: removed "~filters.edited" (pyrogram v2 doesn't have it)
@bot.on_message(filters.command(["mgconcept"]))
async def account_login(bot: Client, m: Message):
    global cancel
    cancel = False
    editable = await m.reply_text(
        "Send **ID & Password** in this manner otherwise bot will not respond.\n\nSend like this:-  **ID*Password**"
    )

    rwa_url = "https://mgconceptapi.classx.co.in/post/userLogin"
    hdr = {
        "Auth-Key": "appxapi",
        "User-Id": "-2",
        "Authorization": "",
        "User_app_category": "",
        "Language": "en",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip, deflate",
        "User-Agent": "okhttp/4.9.1",
    }
    info = {"email": "", "password": ""}

    input1: Message = await bot.listen(editable.chat.id)
    raw_text = input1.text
    info["email"] = raw_text.split("*")[0]
    info["password"] = raw_text.split("*")[1]
    await input1.delete(True)

    scraper = cloudscraper.create_scraper()
    res = scraper.post(rwa_url, data=info, headers=hdr).content
    output = json.loads(res)

    userid = output["data"]["userid"]
    token = output["data"]["token"]

    hdr1 = {
        "Host": "mgconceptapi.classx.co.in",
        "Client-Service": "Appx",
        "Auth-Key": "appxapi",
        "User-Id": userid,
        "Authorization": token,
    }

    await editable.edit("**login Successful**")

    # List courses
    res1 = requests.get(
        f"https://mgconceptapi.classx.co.in/get/mycourse?userid={userid}", headers=hdr1
    )
    b_data = res1.json()["data"]

    cool = ""
    for data in b_data:
        course_name = data["course_name"]
        course_id = data["id"]
        FFF = "**BATCH-ID - BATCH NAME**"
        aa = f" ```{course_id}```      - **{course_name}**\n\n"
        if len(f"{cool}{aa}") > 4096:
            cool = ""
        cool += aa
    await editable.edit(f'{"**You have these batches :-**"}\n\n{FFF}\n\n{cool}')

    # Ask for course id
    editable1 = await m.reply_text("**Now send the Batch ID to Download**")
    input2 = message = await bot.listen(editable.chat.id)
    course_id = input2.text
    await input2.delete(True)
    await editable1.delete(True)

    # Course title
    html = scraper.get(
        f"https://mgconceptapi.classx.co.in/get/course_by_id?id={course_id}", headers=hdr1
    ).json()
    course_title = html["data"][0]["course_name"]

    # Subjects
    html = scraper.get(
        f"https://mgconceptapi.classx.co.in/get/allsubjectfrmlivecourseclass?courseid={course_id}",
        headers=hdr1,
    ).content
    output0 = json.loads(html)
    subjID = output0["data"]

    cool = ""
    vj = ""
    for sub in subjID:
        subjid = sub["subjectid"]
        subjname = sub["subject_name"]
        aa = f" ```{subjid}```      - **{subjname}**\n\n"
        cool += aa
        vj += f"{subjid}&"

    await editable.edit(cool)

    editable1 = await m.reply_text(
        "Now send the **Subject IDs** to Download\n\n"
        "Send like this **1&2&3&4** so on\n"
        "or copy/edit **below ids**:\n\n"
        f"**Enter this to download full batch :-**\n```{vj}```"
    )
    input3 = message = await bot.listen(editable.chat.id)
    subjects_raw = input3.text
    await input3.delete(True)
    await editable1.delete(True)

    prog = await editable.edit("**Extracting Videos Links Please Wait  📥 **")

    try:
        mm = "MgConcept-Institute"
        # For each subject id
        for raw_sub_id in subjects_raw.split("&"):
            raw_sub_id = raw_sub_id.strip()
            if not raw_sub_id:
                continue

            # Proper URL construction (earlier code passed a stray positional arg)
            res3 = requests.get(
                f"https://mgconceptapi.classx.co.in/get/alltopicfrmlivecourseclass?courseid={course_id}&subjectid={raw_sub_id}",
                headers=hdr1,
            )
            b_data2 = res3.json().get("data", [])

            # For each topic in subject
            for data in b_data2:
                topic_name = data["topic_name"]
                topic_id = data["topicid"]

                hdr11 = {
                    "Host": "mgconceptapi.classx.co.in",
                    "Client-Service": "Appx",
                    "Auth-Key": "appxapi",
                    "User-Id": userid,
                    "Authorization": token,
                }

                res4 = requests.get(
                    f"https://mgconceptapi.classx.co.in/get/livecourseclassbycoursesubtopconceptapiv3"
                    f"?courseid={course_id}&subjectid={raw_sub_id}&topicid={topic_id}&start=-1",
                    headers=hdr11,
                ).json()

                topic_items = res4.get("data", [])
                for item in topic_items:
                    title = item.get("Title", "Untitled")

                    # Video link
                    dl_enc = item.get("download_link", "")
                    if dl_enc:
                        try:
                            url = decode(dl_enc)
                            with open(f"{mm} - {course_title}.txt", "a", encoding="utf-8") as f:
                                f.write(f"{title}:{url}\n")
                        except Exception:
                            pass

                    # PDF link
                    pdf_enc = item.get("pdf_link", "")
                    if pdf_enc:
                        try:
                            url = decode(pdf_enc)
                            with open(f"{mm} - {course_title}.txt", "a", encoding="utf-8") as f:
                                f.write(f"{title}:{url}\n")
                        except Exception:
                            pass

        await prog.delete(True)
        await m.reply_document(
            f"{mm} - {course_title}.txt", caption=f"```{mm} - {course_title}```"
        )
        os.remove(f"{mm} - {course_title}.txt")
        await editable.delete(True)

    except Exception as e:
        await m.reply_text(str(e))
