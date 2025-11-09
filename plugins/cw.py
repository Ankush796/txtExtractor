#  MIT License
#  Code edited & fixed for Pyrogram v2 compatibility

import os
import json
import time
import re
import requests
import cloudscraper
from typing import List

from pyromod import listen  # required for .listen()
from pyrogram import Client, filters
from pyrogram.types import Message

# ---- Brightcove constants (as in your original) ----
ACCOUNT_ID = "6206459123001"
BCOV_POLICY = ("BCpkADawqM1474MvKwYlMRZNBPoqkJY-UWm7zE1U769d5r5kqTjG0v8L-THXuVZtdIQJpfMPB37L_"
               "VJQxTKeNeLO2Eac_yMywEgyV9GjFDQ2LTiT4FEiHhKAUvdbx9ku6fGnQKSMB8J5uIDd")
BC_URL = f"https://edge.api.brightcove.com/playback/v1/accounts/{ACCOUNT_ID}/videos"
BC_HDR = {"BCOV-POLICY": BCOV_POLICY}

# ----------------- Helpers -----------------

def safe_name(s: str) -> str:
    """Sanitize a name to be filesystem-safe."""
    s = re.sub(r"[\\/:*?\"<>|#@+]", "_", s)
    s = s.replace("\t", " ").replace("|", "_").replace("\n", " ").strip()
    return s or "file"

def pick_brightcove_src(video_json: dict) -> str:
    """Pick a playable source from Brightcove JSON."""
    sources = video_json.get("sources") or []
    for src in sources:
        url = src.get("src")
        if url and url.startswith("http"):
            return url
    # Fallback: try first src if present
    if sources and sources[0].get("src"):
        return sources[0]["src"]
    raise RuntimeError("No playable source in Brightcove sources")

# ----------------- Command Handler -----------------

@Client.on_message(filters.command("cw"))
async def cw_handler(client: Client, m: Message):
    """
    Careerwill: Login (ID*PASS ya direct token), batch/Topic listing,
    final TXT file with lessonName:link lines (Brightcove/YouTube).
    """
    session = requests.Session()

    # Step 1: Get credential or token
    prompt = ("Send **ID & Password** is tarah: `ID*Password`\n"
              "ya sirf **TOKEN** bhej do (ek line me).")
    editable = await m.reply_text(prompt)
    inp: Message = await client.listen(editable.chat.id)
    raw_text = inp.text.strip() if inp.text else ""
    await inp.delete(True)

    token = None
    if "*" in raw_text:
        email, password = raw_text.split("*", 1)
        login_url = "https://elearn.crwilladmin.com/api/v1/login-other"
        data = {
            "deviceType": "android",
            "password": password,
            "deviceIMEI": "08750aa91d7387ab",
            "deviceModel": "Realme RMX2001",
            "deviceVersion": "R(Android 11.0)",
            "email": email,
            "deviceToken": "dummy_device_token",
        }
        headers = {
            "Host": "elearn.crwilladmin.com",
            "Appver": "1.55",
            "Apptype": "android",
            "Content-Type": "application/json; charset=UTF-8",
            "Accept-Encoding": "gzip, deflate",
            "User-Agent": "okhttp/5.0.0-alpha.2",
            "Connection": "Keep-Alive",
        }
        try:
            r = session.post(login_url, headers=headers, json=data, timeout=15)
            r.raise_for_status()
            j = r.json()
            token = j["data"]["token"]
            await m.reply_text(f"**Login OK. Token:** `{token}`")
        except Exception as e:
            await m.reply_text(f"Login failed: `{e}`")
            return
    else:
        token = raw_text

    if not token:
        await m.reply_text("Token missing.")
        return

    # Step 2: Fetch batches
    try:
        j = session.get(
            f"https://elearn.crwilladmin.com/api/v1/comp/my-batch?&token={token}",
            timeout=20
        ).json()
        batches = j["data"]["batchData"]
    except Exception as e:
        await m.reply_text(f"Batch fetch failed: `{e}`")
        return

    if not batches:
        await m.reply_text("No batches found.")
        return

    # List batches
    lines = ["**BATCH-ID — BATCH NAME — INSTRUCTOR**"]
    for b in batches:
        lines.append(f"```{b['id']}``` — **{b['batchName']}** — {b.get('instructorName','')}")
    await editable.edit("\n".join(lines))

    # Step 3: Ask for batch id
    editable1 = await m.reply_text("**Batch ID bhejo jisse download karna hai.**")
    inp2: Message = await client.listen(editable1.chat.id)
    batch_id = (inp2.text or "").strip()
    await inp2.delete(True)

    # Step 4: Fetch topics for the batch
    try:
        j2 = session.get(
            f"https://elearn.crwilladmin.com/api/v1/comp/batch-topic/{batch_id}"
            f"?type=class&token={token}",
            timeout=20
        ).json()
        topics = j2["data"]["batch_topic"]
        batch_name = j2["data"]["batch_detail"]["name"]
    except Exception as e:
        await m.reply_text(f"Topic fetch failed: `{e}`")
        return

    if not topics:
        await m.reply_text("No topics found in this batch.")
        return

    # Show topic IDs and counts
    topic_ids_join = "&".join(str(t["id"]) for t in topics)
    details_lines = [f"Batch: **{batch_name}**", "", "**TOPIC-ID — TOPIC — VIDEOS**"]
    for t in topics:
        t_id = str(t["id"])
        t_name = t["topicName"]
        # Pull topic details to count classes
        try:
            d = session.get(
                f"https://elearn.crwilladmin.com/api/v1/comp/batch-detail/{batch_id}"
                f"?redirectBy=mybatch&topicId={t_id}&token={token}",
                timeout=20
            ).json()
            classes = d["data"]["class_list"]["classes"] or []
            count = len(classes)
        except Exception:
            count = 0
        details_lines.append(f"```{t_id}``` — **{t_name}** — ({count})")

    await m.reply_text("\n".join(details_lines))
    editable2 = await m.reply_text(
        "Ab **Topic IDs** bhejo is format me: `1&2&3`\n\n"
        f"Pure batch ke liye yeh paste kar do:\n```{topic_ids_join}```"
    )
    inp3: Message = await client.listen(editable2.chat.id)
    topic_ids_raw = (inp3.text or "").strip()
    await inp3.delete(True)

    try:
        topic_ids: List[str] = [x.strip() for x in topic_ids_raw.split("&") if x.strip()]
    except Exception:
        await m.reply_text("Galat Topic IDs format.")
        return

    # Prepare output file
    safe_batch = safe_name(batch_name)
    out_file = f"{safe_batch}.txt"
    if os.path.exists(out_file):
        os.remove(out_file)

    # Step 5: Iterate topics and collect links
    for t_id in topic_ids:
        try:
            dd = session.get(
                f"https://elearn.crwilladmin.com/api/v1/comp/batch-detail/{batch_id}"
                f"?redirectBy=mybatch&topicId={t_id}&token={token}",
                timeout=25
            ).json()
        except Exception as e:
            await m.reply_text(f"Topic `{t_id}` error: `{e}`")
            continue

        class_list = dd.get("data", {}).get("class_list", {})
        topic_name = safe_name(class_list.get("topicName", f"topic_{t_id}"))
        classes = class_list.get("classes") or []
        classes.reverse()  # original behavior

        for cls in classes:
            try:
                vid_id = str(cls["id"])
                lesson_name = safe_name(cls.get("lessonName", f"video_{vid_id}"))
                lesson_url_val = cls.get("lessonUrl") or []
                bcvid = str(lesson_url_val[0]["link"]) if lesson_url_val else ""

                # Build a playable link
                if bcvid.startswith(("62", "63")):
                    # Brightcove flow
                    v_json = session.get(f"{BC_URL}/{bcvid}", headers=BC_HDR, timeout=20).json()
                    video_src = pick_brightcove_src(v_json)

                    auth_json = session.get(
                        f"https://elearn.crwilladmin.com/api/v1/livestreamToken"
                        f"?type=brightcove&vid={vid_id}&token={token}",
                        timeout=15
                    ).json()
                    stoken = auth_json["data"]["token"]
                    final_link = f"{video_src}&bcov_auth={stoken}"
                elif bcvid:
                    # YouTube embed fallback
                    final_link = f"https://www.youtube.com/embed/{bcvid}"
                else:
                    # No link found
                    continue

                with open(out_file, "a", encoding="utf-8") as f:
                    f.write(f"{lesson_name}:{final_link}\n")

            except Exception as e:
                # Skip a single class error, continue next
                await m.reply_text(f"Class skip ({t_id}): `{e}`")
                continue

    # Step 6: (Optional) Notes download list
    try:
        ask_notes = await m.reply_text("Notes chahiye? **y** / **n**")
        inp5: Message = await client.listen(ask_notes.chat.id)
        want_notes = (inp5.text or "").strip().lower() == "y"
        await inp5.delete(True)

        if want_notes:
            notes_json = session.get(
                f"https://elearn.crwilladmin.com/api/v1/comp/batch-notes/{batch_id}"
                f"?topicid={batch_id}&token={token}",
                timeout=25
            ).json()
            notes = notes_json.get("data", {}).get("notesDetails") or []
            notes.reverse()
            for n in notes:
                name = safe_name(n.get("docTitle", "note"))
                url = n.get("docUrl", "")
                if url:
                    with open(out_file, "a", encoding="utf-8") as f:
                        f.write(f"{name}:{url}\n")
    except Exception as e:
        await m.reply_text(f"Notes fetch error: `{e}`")

    # Step 7: Send the file
    if os.path.exists(out_file):
        await m.reply_document(out_file)
    else:
        await m.reply_text("Koi link generate nahi hua.")

    await m.reply_text("Done ✅")
