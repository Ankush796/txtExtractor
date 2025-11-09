# plugins/khan.py

import json
import os
import time
import requests
from pyrogram import Client, filters
from pyrogram.types import Message

# ---------- Local config (no import from main) ----------
COMMAND_PREFIXES = ("/", "~", "?", "!")
_AUTH = os.environ.get("AUTH_USERS", "").strip()
AUTH_USERS = tuple(int(x) for x in _AUTH.split(",") if x.isdigit())

# --------------------------------------------------------

@Client.on_message(
    (filters.chat(AUTH_USERS) if AUTH_USERS else filters.all) &
    filters.private &
    filters.command("khan", prefixes=COMMAND_PREFIXES)
)
async def account_login(client: Client, m: Message):
    """
    Login to Khan Sir (PenPencil) and dump video links into a txt.
    """
    editable = await m.reply_text(
        "Send **ID & Password** like:  `ID*Password`"
    )

    # Wait for creds
    inp: Message = await client.listen(editable.chat.id)
    raw = (inp.text or "").strip()
    await inp.delete(True)

    try:
        username, password = raw.split("*", 1)
        username, password = username.strip(), password.strip()
    except ValueError:
        return await editable.edit("❌ Format galat hai. Use: `ID*Password`")

    # --- Auth step ---
    auth_url = "https://api.penpencil.xyz/v1/oauth/token"
    s = requests.Session()

    base_headers = {
        "Host": "api.penpencil.xyz",
        "client-id": "5f439b64d553cc02d283e1b4",
        "client-version": "21.0",
        "user-agent": "Android",
        "randomid": "385bc0ce778e8d0b",
        "client-type": "MOBILE",
        "device-meta": "{APP_VERSION:19.0,DEVICE_MAKE:Asus,DEVICE_MODEL:ASUS_X00TD,OS_VERSION:6,PACKAGE_NAME:xyz.penpencil.khansirofficial}",
        "content-type": "application/json; charset=UTF-8",
    }

    auth_headers = {
        **base_headers,
        "authorization": "Bearer c5c5e9c5721a1c4e322250fb31825b62f9715a4572318de90cfc93b02a8a8a75",
    }

    payload = {
        "username": username,
        "otp": "",
        "organizationId": "5f439b64d553cc02d283e1b4",
        "password": password,
        "client_id": "system-admin",
        "client_secret": "KjPXuAVfC5xbmgreETNMaL7z",
        "grant_type": "password",
    }

    try:
        r = s.post(auth_url, headers=auth_headers, json=payload, timeout=20)
        r.raise_for_status()
        token = r.json()["data"]["access_token"]
    except Exception as e:
        return await editable.edit(f"❌ Login failed:\n`{e}`")

    await editable.edit("✅ Login successful.\nFetching batches…")

    api_headers = {
        **base_headers,
        "authorization": f"Bearer {token}",
    }

    # --- List batches ---
    params = {
        "mode": "1",
        "batchCategoryIds": "619bedc3394f824a71d8e721",
        "organisationId": "5f439b64d553cc02d283e1b4",
        "page": "1",
        "programId": "5f476e70a64b4a00ddd81379",
    }

    try:
        batches = s.get(
            "https://api.penpencil.xyz/v3/batches/my-batches",
            params=params,
            headers=api_headers,
            timeout=20,
        ).json()["data"]
    except Exception as e:
        return await editable.edit(f"❌ Batches fetch error:\n`{e}`")

    if not batches:
        return await editable.edit("⚠️ No batches found.")

    text = ["**You have these batches:**\n"]
    for b in batches:
        text.append(f"```{b['_id']}```  — **{b['name']}**")
    await editable.edit("\n".join(text))

    # --- Ask for batch id ---
    ask_batch = await m.reply_text("**Send the Batch ID to proceed**")
    inp_batch: Message = await client.listen(ask_batch.chat.id)
    batch_id = (inp_batch.text or "").strip()
    await inp_batch.delete(True)

    # Batch details + subjects
    try:
        details = s.get(
            f"https://api.penpencil.xyz/v3/batches/{batch_id}/details",
            headers=api_headers,
            timeout=20,
        ).json()["data"]
        subjects = details["subjects"]
        batch_name = details["name"]
    except Exception as e:
        return await ask_batch.edit(f"❌ Batch details error:\n`{e}`")

    # Subject IDs list
    subj_ids = "&".join(s["_id"] for s in subjects)
    await ask_batch.edit(f"**Send Subject ID (ya multiple `&` se):**\n```{subj_ids}```")

    inp_subj: Message = await client.listen(m.chat.id)
    subject_id = (inp_subj.text or "").strip()
    await inp_subj.delete(True)

    # Topic tags (acts as groups inside subject)
    try:
        topics = s.get(
            f"https://api.penpencil.xyz/v2/batches/{batch_id}/subject/{subject_id}/topics?page=1",
            headers=api_headers,
            timeout=20,
        ).json()["data"]
    except Exception as e:
        return await m.reply_text(f"❌ Topics fetch error:\n`{e}`")

    tags = "&".join(t["_id"] for t in topics)
    msg = await m.reply_text(
        f"**Enter to download full subject:**\n```{tags}```\n\n(You can trim this list)"
    )

    inp_tags: Message = await client.listen(m.chat.id)
    tag_text = (inp_tags.text or "").strip()
    await inp_tags.delete(True)

    out_name = f"KhanSir-{batch_name}.txt"
    # Clean old file if exists
    try:
        if os.path.exists(out_name):
            os.remove(out_name)
    except Exception:
        pass

    tag_list = [t.strip() for t in tag_text.split("&") if t.strip()]
    await msg.edit("⏬ Collecting video links…")

    # Collect videos for each tag
    for tag in tag_list:
        try:
            # First page to get pagination
            pg0 = s.get(
                f"https://api.penpencil.xyz/v2/batches/{batch_id}/subject/{subject_id}/contents"
                f"?page=1&tag={tag}&contentType=videos",
                headers=api_headers,
                timeout=20,
            ).json()
            total = pg0["paginate"]["totalCount"]
            limit = pg0["paginate"]["limit"]
            pages = (total // limit) + 2

            # Walk pages from last to first (as original code)
            for page in range(1, pages)[::-1]:
                data = s.get(
                    f"https://api.penpencil.xyz/v2/batches/{batch_id}/subject/{subject_id}/contents"
                    f"?page={page}&tag={tag}&contentType=videos",
                    headers=api_headers,
                    timeout=20,
                ).json()["data"]
                data.reverse()

                lines = []
                for item in data:
                    try:
                        title = item["topic"]
                        raw_url = item["url"]
                        # cdn swap (as in original)
                        m3u8 = raw_url.replace("d1d34p8vz63oiq", "d3nzo6itypaz07").replace("mpd", "m3u8").strip()
                        lines.append(f"{title}:{raw_url}")
                    except KeyError:
                        continue

                if lines:
                    with open(out_name, "a", encoding="utf-8") as f:
                        f.write("\n".join(lines) + "\n")

        except Exception as e:
            await m.reply_text(f"⚠️ Tag `{tag}` error:\n`{e}`")
            continue

    try:
        await m.reply_document(out_name)
    except Exception as e:
        return await m.reply_text(f"❌ File send failed:\n`{e}`")

    await m.reply_text("✅ Done")
