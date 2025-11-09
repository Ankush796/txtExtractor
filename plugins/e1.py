#  MIT License
#  (c) original authors; edits for Pyrogram v2 compatibility

import json
import time
import os
import requests
import cloudscraper
from base64 import b64decode
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

from pyrogram import Client as bot, filters
from pyrogram.types import Message

# ---- Pyrogram v2: "edited" filter no longer exists -> create NOT_EDITED ----
NOT_EDITED = filters.create(lambda _, __, m: getattr(m, "edit_date", None) is None)

@bot.on_message(filters.command(["e1"]) & NOT_EDITED)
async def account_login(app: bot, m: Message):
    """
    Flow:
    1) Ask for "ID*Password"
    2) Login -> fetch courses
    3) Ask for course id -> fetch subjects
    4) Ask for subject id -> fetch topics
    5) Ask for topics to download -> decrypt links -> write to txt & send
    """

    editable = await m.reply_text(
        "Send **ID & Password** like:  `ID*Password`"
    )

    # ---- 1) Credentials ----
    input1: Message = await app.listen(editable.chat.id)
    raw_text = input1.text.strip()
    await input1.delete(True)

    try:
        user_id_text, user_pass = raw_text.split("*", 1)
    except ValueError:
        await editable.edit("❌ Format galat hai. Example: `12345*password`")
        return

    # ---- 2) Login ----
    login_url = "https://e1coachingcenterapi.classx.co.in/post/userLogin"
    hdr_login = {
        "Auth-Key": "appxapi",
        "User-Id": "-2",
        "Authorization": "",
        "User_app_category": "",
        "Language": "en",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip, deflate",
        "User-Agent": "okhttp/4.9.1",
    }
    login_form = {"email": user_id_text, "password": user_pass}

    scraper = cloudscraper.create_scraper()
    try:
        res = scraper.post(login_url, data=login_form, headers=hdr_login).content
        output = json.loads(res)
        userid = str(output["data"]["userid"])
        token = output["data"]["token"]
    except Exception as e:
        await editable.edit(f"❌ Login failed: `{e}`")
        return

    hdr_auth = {
        "Host": "e1coachingcenterapi.classx.co.in",
        "Client-Service": "Appx",
        "Auth-Key": "appxapi",
        "User-Id": userid,
        "Authorization": token,
    }

    await editable.edit("✅ Login successful. Fetching your courses...")

    # ---- 3) List courses ----
    try:
        res1 = requests.get(
            "https://e1coachingcenterapi.classx.co.in/get/mycourse",
            params={"userid": userid},
            headers=hdr_auth,
            timeout=20,
        )
        res1.raise_for_status()
        courses = res1.json().get("data", [])
    except Exception as e:
        await m.reply_text(f"❌ Courses fetch error: `{e}`")
        return

    if not courses:
        await m.reply_text("No courses found on this account.")
        return

    lines = ["**You have these courses:**\n\n**COURSE_ID - COURSE NAME**\n"]
    for c in courses:
        lines.append(f"```{c['id']}``` - **{c['course_name']}**")
    await editable.edit("\n".join(lines))

    editable1 = await m.reply_text("**Now send the Course ID to proceed**")
    input2: Message = await app.listen(editable1.chat.id)
    course_id = input2.text.strip()
    await input2.delete(True)

    # ---- 4) Subjects for the selected course ----
    try:
        subj_res = scraper.get(
            "https://e1coachingcenterapi.classx.co.in/get/allsubjectfrmlivecourseclass",
            params={"courseid": course_id},
            headers=hdr_auth,
            timeout=20,
        ).content
        subj_json = json.loads(subj_res)
        subjects = subj_json.get("data", [])
    except Exception as e:
        await m.reply_text(f"❌ Subjects fetch error: `{e}`")
        return

    if not subjects:
        await m.reply_text("No subjects found for this course.")
        return

    await m.reply_text("Subjects raw JSON (for reference):\n(This is long; just pick the subject id from it)")
    await m.reply_text(str(subjects)[:4000])

    editable_sub = await m.reply_text("**Enter the Subject ID (as shown above)**")
    input3: Message = await app.listen(editable_sub.chat.id)
    subject_id = input3.text.strip()
    await input3.delete(True)

    # ---- 5) Topics list (IMPORTANT BUG FIX: correct URL with params) ----
    try:
        res3 = requests.get(
            "https://e1coachingcenterapi.classx.co.in/get/alltopicfrmlivecourseclass",
            params={"courseid": course_id, "subjectid": subject_id},
            headers=hdr_auth,
            timeout=20,
        )
        res3.raise_for_status()
        topics = res3.json().get("data", [])
    except Exception as e:
        await m.reply_text(f"❌ Topics fetch error: `{e}`")
        return

    if not topics:
        await m.reply_text("No topics found for this subject.")
        return

    # Build IDs string for full-batch suggestion
    ids_joined = "&".join(str(t["topicid"]) for t in topics)
    topic_lines = ["**TOPIC-ID  -  TOPIC  -  (count is ID length here)**\n"]
    for t in topics:
        tid = str(t["topicid"])
        tname = t["topic_name"]
        topic_lines.append(f"```{tid}``` - **{tname} - ({len(tid)})**")
    await m.reply_text("\n".join(topic_lines))

    editable_ids = await m.reply_text(
        f"Now send **Topic IDs** to download (like `1&2&3`).\n\n"
        f"**Full batch IDs:**\n```{ids_joined}```"
    )
    input4: Message = await app.listen(editable_ids.chat.id)
    wanted_ids_raw = input4.text.strip()
    await input4.delete(True)

    # ---- 6) Resolution (kept because tumhare flow me tha) ----
    editable_res = await m.reply_text("**Now send the Resolution**")
    input5: Message = await app.listen(editable_res.chat.id)
    _resolution = input5.text.strip()  # not used in link generation but kept for compatibility
    await input5.delete(True)

    wanted_ids = [x for x in wanted_ids_raw.split("&") if x.strip()]
    if not wanted_ids:
        await m.reply_text("❌ No topic ids provided.")
        return

    out_name = "E1-Coaching-Center.txt"
    # ensure clean file
    if os.path.exists(out_name):
        try:
            os.remove(out_name)
        except Exception:
            pass

    try:
        for tid in wanted_ids:
            # classes for a topic
            res4 = requests.get(
                "https://e1coachingcenterapi.classx.co.in/get/livecourseclassbycoursesubtopconceptapiv3",
                params={
                    "topicid": tid,
                    "start": -1,
                    "conceptid": 1,
                    "courseid": course_id,
                    "subjectid": subject_id,
                },
                headers=hdr_auth,
                timeout=30,
            ).json()

            items = res4.get("data", [])
            for item in items:
                # they sometimes fill either 'embed_url' or 'pdf_link'
                b64 = item.get("embed_url") or item.get("pdf_link") or ""
                title = item.get("Title", "Untitled")

                # decrypt (same as your logic)
                try:
                    key = "638udh3829162018".encode("utf8")
                    iv = "fedcba9876543210".encode("utf8")
                    ciphertext = bytearray.fromhex(b64decode(b64.encode()).hex())
                    cipher = AES.new(key, AES.MODE_CBC, iv)
                    plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
                    link = plaintext.decode("utf-8")
                except Exception:
                    # fallback: if not decryptable, just keep raw (prevents crash)
                    link = b64

                with open(out_name, "a", encoding="utf-8") as f:
                    f.write(f"{title}:{link}\n")

        await m.reply_document(out_name)
    except Exception as e:
        await m.reply_text(f"❌ Error while building links: `{e}`")
        return
    finally:
        time.sleep(1)

    await m.reply_text("✅ Done")
