import os
import asyncio
from pyrogram import Client, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # Example: -100xxxxxxxxxx
OWNER_ID = int(os.getenv("OWNER_ID"))      # Your Telegram User ID (int)

app = Client("auto_invite_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
scheduler = AsyncIOScheduler()

# Function to auto-create and revoke links
async def refresh_invite_link():
    try:
        async with app:
            # Revoke all old invite links
            invite_links = await app.get_chat_invite_links(CHANNEL_ID, revoke=True)
            for link in invite_links:
                await app.revoke_chat_invite_link(CHANNEL_ID, link.invite_link)

            # Create new one
            new_link = await app.create_chat_invite_link(CHANNEL_ID, creates_join_request=False)

            # Send to owner
            await app.send_message(
                OWNER_ID,
                f"""**[ Channel Invite Updated ]**

🔗 **New Link:** [`{new_link.invite_link}`]({new_link.invite_link})
⏱️ **Refreshed At:** `{new_link.created_at.strftime("%Y-%m-%d %H:%M:%S")}`
♻️ **Old link revoked automatically**

~ Powered by **Bidu Bot System**""",
                disable_web_page_preview=True
            )
            print(f"[+] Sent new invite to owner: {new_link.invite_link}")

    except Exception as e:
        print(f"[!] Error while refreshing: {e}")

# Manual command to start the schedule (optional)
@app.on_message(filters.private & filters.user(OWNER_ID) & filters.command("start"))
async def start_bot(client, message):
    if not scheduler.running:
        scheduler.add_job(refresh_invite_link, "interval", minutes=1)
        scheduler.start()
        await message.reply("✅ Bidu Bot Activated!\nAuto invite link will refresh every 1 minute.")
    else:
        await message.reply("⚙️ Already running bhai.")

app.run()
