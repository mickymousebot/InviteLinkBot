import os
import asyncio
from pyrogram import Client, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
OWNER_ID = int(os.getenv("OWNER_ID"))
LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID"))

app = Client("auto_invite_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
scheduler = AsyncIOScheduler()

# Stylish message template
def format_invite_message(link):
    return f"""**[ Channel Invite Updated ]**

🔗 **New Link:** [`{link.invite_link}`]({link.invite_link})
⏱️ **Refreshed At:** `{link.created_at.strftime("%Y-%m-%d %H:%M:%S")}`
♻️ **Old link revoked automatically**

~ Powered by **Bidu Bot System**
"""

# Common function for both auto and command
async def generate_and_send_invite():
    try:
        # Revoke all old links
        invite_links = await app.get_chat_invite_links(CHANNEL_ID, revoke=True)
        for l in invite_links:
            await app.revoke_chat_invite_link(CHANNEL_ID, l.invite_link)

        # Create fresh link
        new_link = await app.create_chat_invite_link(CHANNEL_ID, creates_join_request=False)

        # Send to owner and log group
        message = format_invite_message(new_link)
        await app.send_message(OWNER_ID, message, disable_web_page_preview=True)
        await app.send_message(LOG_GROUP_ID, message, disable_web_page_preview=True)

        print(f"[+] New invite link sent to owner and group.")
    except Exception as e:
        print(f"[!] Error: {e}")

# Scheduled auto task
async def scheduled_task():
    await generate_and_send_invite()

# Manual /newlink command
@app.on_message(filters.private & filters.user(OWNER_ID) & filters.command("newlink"))
async def manual_link_command(client, message):
    await generate_and_send_invite()
    await message.reply("✅ New invite link generated and sent.")

# /start command to start the scheduler
@app.on_message(filters.private & filters.user(OWNER_ID) & filters.command("start"))
async def start_scheduler(client, message):
    if not scheduler.running:
        scheduler.add_job(scheduled_task, "interval", minutes=1)
        scheduler.start()
        await message.reply("✅ Bidu Bot Activated! Auto link refresh started.")
    else:
        await message.reply("⚙️ Already running bhai.")

app.run()
