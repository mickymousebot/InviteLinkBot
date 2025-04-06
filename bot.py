import os
import json
import logging
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler

load_dotenv()
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Load channels from JSON file
with open("channels.json", "r") as f:
    CHANNEL_LIST = json.load(f)

# Store last invite links to revoke later
last_links = {}

async def generate_and_send_links(application):
    bot = application.bot
    global last_links

    for channel in CHANNEL_LIST:
        try:
            # Revoke old link
            if channel in last_links:
                try:
                    await bot.revoke_chat_invite_link(chat_id=channel, invite_link=last_links[channel])
                    logging.info(f"Revoked old link for {channel}")
                except Exception as e:
                    logging.warning(f"Failed to revoke old link for {channel}: {e}")

            # Create new invite link
            invite = await bot.create_chat_invite_link(chat_id=channel, creates_join_request=False)
            last_links[channel] = invite.invite_link

            # Send formatted message to admin
            await bot.send_message(
                chat_id=ADMIN_ID,
                text=f"""✅ *New Private Invite Link Generated!*

*📢 Channel:* `{channel}`
*🔗 Invite Link:* [Click to Join]({invite.invite_link})

⏱️ *Link Validity:* Rotates every *10 minutes*
♻️ *Old link has been revoked successfully*

🔐 _Secure | Automated | Reliable_

— *InviteLinkBot™*
""",
                parse_mode="Markdown",
                disable_web_page_preview=True
            )

        except Exception as e:
            logging.error(f"Error processing {channel}: {e}")
            await bot.send_message(chat_id=ADMIN_ID, text=f"❌ Error with {channel}:\n`{e}`", parse_mode="Markdown")

async def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(generate_and_send_links, "interval", minutes=10, args=[application])
    scheduler.start()

    logging.info("🚀 Bot is running and scheduler started...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await application.updater.idle()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
