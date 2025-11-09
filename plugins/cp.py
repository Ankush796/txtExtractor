#  MIT License
#  Code edited By Cryptostark (fixed for Pyrogram v2 compatibility)

import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from pyromod import listen  # needs pyromod>=2.0.0b11 with Pyrogram v2
import os

# NOTE:
# - filters.edited hata diya (Pyrogram v2 me nahi hota)
# - galat imports hata diye
# - id2 vs id1 typo fix
# - unnecessary duplicates clean

@Client.on_message(filters.command(["cp"]))
async def account_login(client: Client, m: Message):
    s = requests.Session()
    editable = await m.reply_text("**Send Token from ClassPlus App**")
    input1: Message = await client.listen(editable.chat.id)
    raw_text0 = input1.text.strip()

    headers = {
        'authority': 'api.classplusapp.com',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en',
        'api-version': '28',
        'cache-control': 'no-cache',
        'device-id': '516',
        'origin': 'https://web.classplusapp.com',
        'pragma': 'no-cache',
        'referer': 'https://web.classplusapp.com/',
        'region': 'IN',
        'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
        'x-access-token': raw_text0
    }

    resp = s.get(
        'https://api.classplusapp.com/v2/batches/details?limit=20&offset=0&sortBy=createdAt',
        headers=headers
    )

    if resp.status_code != 200:
        await editable.edit("**Login Failed — token invalid ya expired.**")
        return

    b_data = resp.json()["data"]["totalBatches"]
    await input1.delete(True)

    FFF = "**BATCH-ID - BATCH NAME**"
    lines = []
    for data in b_data:
        t_name = data.get('batchName')
        t_id = data.get('batchId')
        lines.append(f"```{t_id}```  - **{t_name}**")

    await editable.edit(f'**You have these batches :-**\n\n{FFF}\n\n' + "\n\n".join(lines))

    editable1 = await m.reply_text("**Now send the Batch (Course) ID to Download**")
    input2: Message = await client.listen(editable.chat.id)
    cr = input2.text.strip()
    await editable1.delete(True)

    resp = s.get(f'https://api.classplusapp.com/v2/course/content/get?courseId={cr}', headers=headers)
    course = resp.json().get('data', {}).get('courseContent', [])

    FFF = "**FOLDER-ID - FOLDER NAME**"
    lines = []
    for data in course:
        id1 = data.get('id')
        nam2 = data.get("name")
        lines.append(f"```{id1}``` - **{nam2}**")

    await editable.edit(f'**You have these Folders :-**\n\n{FFF}\n\n' + "\n\n".join(lines))

    editable2 = await m.reply_text("**Now send the Folder ID to List**")
    input3: Message = await client.listen(editable.chat.id)
    folder_id_lvl1 = input3.text.strip()
    await editable2.delete(True)

    resp = s.get(
        f'https://api.classplusapp.com/v2/course/content/get?courseId={cr}&folderId={folder_id_lvl1}',
        headers=headers
    )
    lvl1 = resp.json().get('data', {}).get('courseContent', [])

    FFF = "**FOLDER-ID - FOLDER NAME - TOTAL VIDEOS/PDFS**"
    lines = []
    for data in lvl1:
        id1 = data.get('id')
        nam2 = data.get("name")
        vid = data.get("resources", {}).get("videos")
        fid = data.get("resources", {}).get("files")
        lines.append(f"```{id1}``` - **{nam2} - {vid} - {fid}**")

    await editable.edit(f'**You have these Folders :-**\n\n{FFF}\n\n' + "\n\n".join(lines))

    editable3 = await m.reply_text("**Now send the Folder ID to Download**")
    input4: Message = await client.listen(editable.chat.id)
    folder_id_lvl2 = input4.text.strip()
    await editable3.delete(True)

    respc = s.get(
        f'https://api.classplusapp.com/v2/course/content/get?courseId={cr}&folderId={folder_id_lvl2}',
        headers=headers
    ).json()

    ddata = respc.get('data', {}).get('courseContent', [])
    if not ddata:
        await editable.edit("**This folder is empty or inaccessible.**")
        return

    # contentType==1 => nested folders; else => items (videos/files)
    if ddata[0].get("contentType") == 1:
        # list inner folders
        FFF = "**FOLDER-ID - FOLDER NAME - TOTAL VIDEOS/PDFS**"
        lines = []
        for datas in ddata:
            id2 = datas.get('id')
            nam2 = datas.get("name")
            vid2 = datas.get("resources", {}).get("videos")
            fid2 = datas.get("resources", {}).get("files")
            lines.append(f"```{id2}``` - **{nam2} - {vid2} - {fid2}**")

        await editable.edit(f'**You have these Folders :-**\n\n{FFF}\n\n' + "\n\n".join(lines))

        # ask final folder to open
        editable4 = await m.reply_text("**Now send the final Folder ID to list topics**")
        input5: Message = await client.listen(editable.chat.id)
        folder_id_lvl3 = input5.text.strip()
        await editable4.delete(True)

        resp = s.get(
            f'https://api.classplusapp.com/v2/course/content/get?courseId={cr}&folderId={folder_id_lvl3}',
            headers=headers
        )
        bdat = resp.json().get('data', {}).get('courseContent', [])
        bdat.reverse()

        FFF = "**Topic-ID - Topic NAME**"
        lines = []
        txt_name = "careerplus1.txt"
        # fresh file
        if os.path.exists(txt_name):
            os.remove(txt_name)

        for data in bdat:
            id1 = data.get('id')
            nam2 = data.get("name")
            dis2 = data.get("description")
            url2 = data.get("url")
            lines.append(f"```{id1}``` - **{nam2} - {dis2}**")
            with open(txt_name, "a", encoding="utf-8") as f:
                f.write(f"{nam2}-{dis2}:{url2}\n")

        await m.reply_document(txt_name)
        await editable.edit(f'**You have these Videos :-**\n\n{FFF}\n\n' + "\n\n".join(lines))

    else:
        # direct items in this folder
        ddata.reverse()
        FFF = "**Topic-ID - Topic NAME**"
        lines = []
        txt_name = "classplus.txt"
        if os.path.exists(txt_name):
            os.remove(txt_name)

        for data in ddata:
            id2 = str(data.get('id'))
            nam2 = data.get("name")
            url2 = data.get("url")
            des2 = data.get("description")
            lines.append(f"```{id2}``` - **{nam2} - {des2}**")
            with open(txt_name, "a", encoding="utf-8") as f:
                f.write(f"{nam2}-{des2}:{url2}\n")

        await m.reply_document(txt_name)
        await editable.edit(f'**You have these Videos :-**\n\n{FFF}\n\n' + "\n\n".join(lines))
        await m.reply_text("**Now Press /cpd to Download **")
