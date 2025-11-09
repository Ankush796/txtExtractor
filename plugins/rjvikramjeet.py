#  MIT License
#  Code edited & fixed for Pyrogram v2

import json
import os
import requests
import cloudscraper

from base64 import b64decode
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

from pyrogram import Client as bot, filters
from pyrogram.types import Message
from pyromod import listen  # enable Client.listen()

# --------- helpers ---------
def decode_b64_cbc(token: str) -> str:
    """Decrypt ClassX AES/CBC base64 payload to URL."""
    key = "638udh3829162018".encode("utf-8")
    iv = "fedcba9876543210".encode("utf-8")
    ciphertext = bytearray.fromhex(b64decode(token.encode()).hex())
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
    return plaintext.decode("utf-8")

# --------- command ---------
@bot.on_message(filters.command(["rgvikramjeet"]))
async def rgvikramjeet_login(client: bot, m: Message):
    session = requests.Session()
    editable = await m.reply_text(
        "Send **ID & Password** like this:\n\n`ID*Password`"
    )

    # Take creds
    inp: Message = await client.listen(editable.chat.id)
    raw = (inp.text or "").strip()
    await inp.delete(True)

    try:
        email, password = raw.split("*", 1)
    except ValueError:
        await editable.edit("❌ Invalid format. Use: `ID*Password`")
        return

    # Login
    login_url = "https://rgvikramjeetapi.classx.co.in/post/userLogin"
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
    payload = {"email": email, "password": password}

    scraper = cloudscraper.create_scraper()
    try:
        res = scraper.post(login_url, data=payload, headers=hdr_login).json()
        user_id = res["data"]["userid"]
        token = res["data"]["token"]
    except Exception as e:
        await editable.edit(f"❌ Login failed: {e}")
        return

    hdr_auth = {
        "Host": "rgvikramjeetapi.classx.co.in",
        "Client-Service": "Appx",
        "Auth-Key": "appxapi",
        "User-Id": str(user_id),
        "Authorization": token,
    }

    await editable.edit("✅ Login Successful. Fetching courses...")

    # List courses
    try:
        r = session.get(
            f"https://rgvikramjeetapi.classx.co.in/get/mycourse?userid={user_id}",
            headers=hdr_auth,
        )
        courses = r.json()["data"]
    except Exception as e:
        await m.reply_text(f"❌ Could not fetch courses: {e}")
        return

    course_lines = []
    for c in courses:
        course_lines.append(f"```{c['id']}```  - **{c['course_name']}**")
    await editable.edit("**You have these batches :-**\n\n" + "\n\n".join(course_lines))

    # Ask course id
    ask_course: Message = await m.reply_text("**Now send the Batch ID to Download**")
    course_msg = await client.listen(ask_course.chat.id)
    course_id = (course_msg.text or "").strip()
    await course_msg.delete(True)
    await ask_course.delete(True)

    # Course title
    try:
        course_meta = scraper.get(
            f"https://rgvikramjeetapi.classx.co.in/get/course_by_id?id={course_id}",
            headers=hdr_auth,
        ).json()
        course_title = course_meta["data"][0]["course_name"]
    except Exception:
        course_title = course_id

    # List subjects
    try:
        subj_resp = scraper.get(
            f"https://rgvikramjeetapi.classx.co.in/get/allsubjectfrmlivecourseclass?courseid={course_id}",
            headers=hdr_auth,
        ).json()
        subjects = subj_resp["data"]
    except Exception as e:
        await m.reply_text(f"❌ Could not fetch subjects: {e}")
        return

    subj_ids_concat = ""
    subj_lines = []
    for s in subjects:
        sid = s["subjectid"]
        subj_ids_concat += f"{sid}&"
        subj_lines.append(f"```{sid}```  -  **{s['subject_name']}**")

    await editable.edit("\n".join(subj_lines))

    ask_subj: Message = await m.reply_text(
        "Now send **Subject IDs** like `id1&id2&id3` (or paste the list shown above):\n\n"
        f"**Full batch shortcut:**\n```{subj_ids_concat}```"
    )
    subj_msg = await client.listen(ask_subj.chat.id)
    subj_ids_raw = (subj_msg.text or "").strip().strip("&")
    await subj_msg.delete(True)
    await ask_subj.delete(True)

    prog = await editable.edit("📥 **Extracting video links… please wait**")

    out_txt = f"Rgvikramjeet - {course_title}.txt"
    out_json = f"{course_title}.json"
    # clean old files if redeploying/rerunning
    for p in (out_txt, out_json):
        try:
            if os.path.exists(p):
                os.remove(p)
        except:
            pass

    output_dict = {}
    try:
        for subj_id in [x for x in subj_ids_raw.split("&") if x.strip()]:
            # topics under subject
            try:
                topics = session.get(
                    "https://rgvikramjeetapi.classx.co.in/get/alltopicfrmlivecourseclass",
                    params={"courseid": course_id, "subjectid": subj_id},
                    headers=hdr_auth,
                ).json()["data"]
            except Exception as e:
                await m.reply_text(f"⚠️ Subject {subj_id} topics error: {e}")
                continue

            for topic in topics:
                topic_name = topic["topic_name"]
                topic_id = topic["topicid"]

                # concepts under topic
                try:
                    concepts = session.get(
                        "https://rgvikramjeetapi.classx.co.in/get/allconceptfrmlivecourseclass",
                        params={
                            "courseid": course_id,
                            "subjectid": subj_id,
                            "topicid": topic_id,
                            "start": "-1",
                        },
                        headers=hdr_auth,
                    ).json()["data"]
                except Exception as e:
                    await m.reply_text(f"⚠️ Concepts error ({topic_name}): {e}")
                    continue

                videos_map = {}
                for concept in concepts:
                    concept_id = concept["conceptid"]
                    # classes under concept
                    try:
                        classes = session.get(
                            "https://rgvikramjeetapi.classx.co.in/get/livecourseclassbycoursesubtopconceptapiv3",
                            params={
                                "courseid": course_id,
                                "subjectid": subj_id,
                                "topicid": topic_id,
                                "conceptid": concept_id,
                                "start": "-1",
                            },
                            headers=hdr_auth,
                        ).json()["data"]
                    except Exception as e:
                        await m.reply_text(f"⚠️ Classes error ({topic_name}): {e}")
                        continue

                    for cls in classes:
                        title = cls.get("Title", "Untitled")
                        enc = cls.get("download_link") or cls.get("pdf_link") or ""
                        if not enc:
                            continue
                        try:
                            url = decode_b64_cbc(enc)
                        except Exception:
                            # if decrypt fails, just keep the raw token
                            url = enc

                        videos_map[title] = url
                        with open(out_txt, "a", encoding="utf-8") as f:
                            f.write(f"{title}:{url}\n")

                if videos_map:
                    output_dict[topic_name] = videos_map

        # dump json too
        with open(out_json, "w", encoding="utf-8") as jf:
            json.dump(output_dict, jf, ensure_ascii=False, indent=2)

        await prog.delete(True)
        if os.path.exists(out_json):
            await m.reply_document(out_json, caption=f"```{out_json}```")
        if os.path.exists(out_txt):
            await m.reply_document(out_txt, caption=f"```{out_txt[:-4]}```")

    except Exception as e:
        await m.reply_text(f"❌ Unexpected error: {e}")
