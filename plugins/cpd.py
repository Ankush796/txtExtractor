#  MIT License (header same)
import os, time, subprocess, requests
from pyromod import listen  # patches Client.listen
from pyrogram import Client, filters
from pyrogram.types import Message
from subprocess import getstatusoutput
import helper

CLASSPLUS_TOKEN = os.environ.get("CLASSPLUS_TOKEN", "").strip()

@Client.on_message(filters.command(["cpd"]))
async def account_login(client: Client, m: Message):
    editable = await m.reply_text("Send txt file**")
    input_msg: Message = await client.listen(editable.chat.id)
    txt_path = await input_msg.download()
    await input_msg.delete(True)

    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            content = f.read().strip().splitlines()
        links = [i.split(":", 1) for i in content if ":" in i]
        os.remove(txt_path)
    except Exception:
        await m.reply_text("Invalid file input.")
        if os.path.exists(txt_path):
            os.remove(txt_path)
        return

    editable = await m.reply_text(
        f"Total links found are **{len(links)}**\n\nSend start index (default **0**)"
    )
    input1: Message = await client.listen(editable.chat.id)
    try:
        start_idx = int(input1.text.strip())
    except Exception:
        start_idx = 0
    await input1.delete(True)

    editable2 = await m.reply_text("**Enter Title**")
    input0: Message = await client.listen(editable.chat.id)
    common_caption = input0.text.strip()
    await input0.delete(True)

    await m.reply_text("**Enter resolution (info only)**")
    input2: Message = await client.listen(editable.chat.id)
    _resolution = input2.text.strip()
    await input2.delete(True)

    editable4 = await m.reply_text(
        "Now send the **Thumb url**\nEg : `https://telegra.ph/file/d9e2...jpg`\n\nor send **no**"
    )
    input6: Message = await client.listen(editable.chat.id)
    thumb = input6.text.strip()
    await input6.delete(True)

    if thumb.lower() not in ("no", "n"):
        getstatusoutput(f"wget '{thumb}' -O 'thumb.jpg'")
        thumb_path = "thumb.jpg"
    else:
        thumb_path = None

    count = start_idx + 1

    for i in range(start_idx, len(links)):
        try:
            name1 = (
                links[i][0]
                .replace("\t", "")
                .replace(":", "")
                .replace("/", "")
                .replace("+", "")
                .replace("#", "")
                .replace("|", "")
                .replace("@", "")
                .replace("*", "")
                .replace(".", "")
                .strip()
            )
            url = links[i][1].strip()

            # Resolve JW signed URL only if token available and link is classplus
            url1 = url
            if CLASSPLUS_TOKEN and "classplus" in url:
                hdr = {
                    "Host": "api.classplusapp.com",
                    "x-access-token": CLASSPLUS_TOKEN,
                    "user-agent": "Mobile-Android",
                    "app-version": "1.4.37.1",
                    "api-version": "18",
                }
                r = requests.get(
                    "https://api.classplusapp.com/cams/uploader/video/jw-signed-url",
                    headers=hdr,
                    params={"url": url},
                    timeout=20,
                )
                r.raise_for_status()
                a = r.json().get("url", url)
                r2 = requests.get(a, headers={"User-Agent": "ExoPlayerDemo"}, timeout=20)
                r2.raise_for_status()
                # 3rd line of m3u8 master
                url1 = r2.text.splitlines()[2] if len(r2.text.splitlines()) >= 3 else url

            name = f"{str(count).zfill(3)}) {name1}"
            show = f"**Downloading:-**\n\n**Name :-** `{name}`\n\n**Url :-** `{url1}`"
            prog = await m.reply_text(show)

            cc = f"**Title »** {name1}.mkv\n**Caption »** {common_caption}\n**Index »** {str(count).zfill(3)}"

            if url1.lower().endswith(".pdf"):
                cmd = f'yt-dlp -o "{name}.pdf" "{url1}"'
            else:
                cmd = f'yt-dlp -o "{name}.mp4" --no-keep-video --no-check-certificate --remux-video mkv "{url1}"'

            download_cmd = f"{cmd} -R 25 --fragment-retries 25 --external-downloader aria2c --downloader-args 'aria2c: -x 16 -j 32'"
            os.system(download_cmd)

            filename = None
            for ext in (".mkv", ".mp4", ".pdf"):
                f = f"{name}{ext}"
                if os.path.isfile(f):
                    filename = f
                    break

            if not filename:
                await prog.delete()
                await m.reply_text(f"**Downloading failed ❌**\nName - {name}\nLink - `{url1}`")
                count += 1
                continue

            if filename.endswith(".pdf"):
                await prog.delete()
                await m.reply_document(filename, caption=cc)
                os.remove(filename)
                count += 1
                continue

            # make thumb if needed
            thumb_for_upload = thumb_path
            if not thumb_for_upload:
                thumb_jpg = f"{filename}.jpg"
                subprocess.run(
                    f'ffmpeg -i "{filename}" -ss 00:01:00 -vframes 1 "{thumb_jpg}"',
                    shell=True,
                )
                if os.path.isfile(thumb_jpg):
                    thumb_for_upload = thumb_jpg

            await prog.delete()
            reply = await m.reply_text(f"Uploading - ```{name}```")

            dur = int(helper.duration(filename))
            start_time = time.time()

            await m.reply_video(
                filename,
                supports_streaming=True,
                height=720,
                width=1280,
                caption=cc,
                duration=dur,
                thumb=thumb_for_upload if thumb_for_upload else None,
            )

            count += 1
            os.remove(filename)
            if thumb_for_upload and thumb_for_upload.endswith(".jpg"):
                try:
                    os.remove(thumb_for_upload)
                except Exception:
                    pass

            await reply.delete()
            time.sleep(1)

        except Exception as e:
            await m.reply_text(
                f"**downloading failed ❌**\n{str(e)}\n**Name** - {name1}\n**Link** - `{url}`"
            )
            continue

    await m.reply_text("Done ✅")
