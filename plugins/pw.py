import requests
from subprocess import getstatusoutput
from pyromod import listen  # enables bot.listen(...)
from pyrogram import Client as bot, filters
from pyrogram.types import Message


@bot.on_message(filters.command(["pw"]))
async def account_login(app: bot, m: Message):
    # 1) Token maango
    editable = await m.reply_text(
        "Send **Auth code** (PhysicsWallah app ka Authorization token):\n\n`AUTH_CODE`"
    )
    token_msg: Message = await app.listen(editable.chat.id)
    auth_code = token_msg.text.strip()
    await token_msg.delete(True)

    # 2) Common headers
    headers = {
        "Host": "api.penpencil.xyz",
        "authorization": f"Bearer {auth_code}",
        "client-id": "5eb393ee95fab7468a79d189",
        "client-version": "12.84",
        "user-agent": "Android",
        "randomid": "e4307177362e86f1",
        "client-type": "MOBILE",
        # NOTE: package name string doesn’t matter for our flow, just keep consistent
        "device-meta": "{APP_VERSION:12.84,DEVICE_MAKE:Asus,DEVICE_MODEL:ASUS_X00TD,OS_VERSION:6,PACKAGE_NAME:xyz.penpencil.physicswallah}",
        "content-type": "application/json; charset=UTF-8",
    }

    # 3) Batches dikhao
    await editable.edit("**Your Batches (BatchName : BatchID)**")
    params = {
        "mode": "1",
        "filter": "false",
        "exam": "",
        "amount": "",
        "organisationId": "5eb393ee95fab7468a79d189",
        "classes": "",
        "limit": "20",
        "page": "1",
        "programId": "",
        "ut": "1652675230446",
    }
    batches = requests.get(
        "https://api.penpencil.xyz/v3/batches/my-batches", params=params, headers=headers
    ).json()["data"]

    if not batches:
        return await m.reply_text("No batches found for this auth code.")

    for b in batches:
        await m.reply_text(f"```{b['name']}```  :  ```{b['_id']}```")

    # 4) Batch ID lo
    ask_batch = await m.reply_text("**Now send the Batch ID to proceed**")
    msg_batch: Message = await app.listen(ask_batch.chat.id)
    batch_id = msg_batch.text.strip()
    await msg_batch.delete(True)

    # 5) Batch details nikaalo (subjects + batch name)
    details = requests.get(
        f"https://api.penpencil.xyz/v3/batches/{batch_id}/details", headers=headers
    ).json()["data"]
    batch_name = details.get("name", "PW-Batch")
    subjects = details.get("subjects", [])

    if not subjects:
        return await m.reply_text("No subjects found in this batch.")

    # 6) Subjects list + subject IDs for full download
    subj_ids_concat = ""
    lines = []
    for s in subjects:
        lines.append(f"```{s['_id']}```")
        subj_ids_concat += f"{s['_id']}&"

    await ask_batch.edit(
        "**Subjects (copy-paste IDs as needed):**\n" + "\n".join(lines)
    )

    ask_all = await m.reply_text(
        f"**Enter this to download full batch:**\n```{subj_ids_concat}```\n\nOr paste selected subject IDs separated by `&`"
    )
    msg_subj: Message = await app.listen(ask_all.chat.id)
    subjects_input = msg_subj.text.strip()
    await msg_subj.delete(True)

    # 7) Optional inputs (resolution currently unused, kept for compatibility)
    ask_res = await m.reply_text("**Enter resolution (e.g., 480/720) — optional**")
    msg_res: Message = await app.listen(ask_res.chat.id)
    _resolution = msg_res.text.strip()
    await msg_res.delete(True)

    ask_thumb = await m.reply_text(
        "Send **Thumb URL** (e.g. `https://telegra.ph/file/d9e2...jpg`) or send `no`"
    )
    msg_thumb: Message = await app.listen(ask_thumb.chat.id)
    thumb = msg_thumb.text.strip()
    await msg_thumb.delete(True)

    if thumb.lower() != "no" and (thumb.startswith("http://") or thumb.startswith("https://")):
        getstatusoutput(f"wget '{thumb}' -O 'thumb.jpg'")
        thumb = "thumb.jpg"
    else:
        thumb = "no"

    # 8) Har subject ke contents se video URLs gather karo
    try:
        out_txt = f"{batch_name}.txt"
        open(out_txt, "w").close()  # reset file

        subj_ids = [s for s in subjects_input.split("&") if s.strip()]
        for subj_id in subj_ids:
            subj_id = subj_id.strip()
            # 4 pages try karte hain (jitna original script me tha)
            for page in ("1", "2", "3", "4"):
                params_contents = {
                    "page": page,
                    "tag": "",
                    "contentType": "exercises-notes-videos",
                    "ut": "",
                }
                data = requests.get(
                    f"https://api.penpencil.xyz/v2/batches/{batch_id}/subject/{subj_id}/contents",
                    params=params_contents,
                    headers=headers,
                ).json().get("data", [])

                # reverse jaisa old code me tha
                try:
                    data = list(data)
                except Exception:
                    data = []
                # write every video's transformed URL
                for item in data:
                    try:
                        title = item.get("topic", "Untitled")
                        url = item.get("url", "").replace(
                            "d1d34p8vz63oiq", "d3nzo6itypaz07"
                        ).replace("mpd", "m3u8").strip()
                        if not url:
                            continue
                        with open(out_txt, "a") as f:
                            f.write(f"{title}:{url}\n")
                    except Exception:
                        continue

        await m.reply_document(out_txt)
    except Exception as e:
        await m.reply_text(f"Error: `{e}`")
