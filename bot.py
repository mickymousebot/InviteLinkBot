import os
import json
import logging
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Load .env variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Load channel list
with open("channels.json", "r") as file:
    CHANNELS = json.load(file)

# Store last invite links
last_links = {}

# Function to create and send new invite links
async def generate_links(app):
    bot = app.bot
    global last_links

    for channel in CHANNELS:
        try:
            # Revoke all active invite links
            try:
                active_links = await bot.get_chat_invite_links(chat_id=channel, creates_join_request=False, limit=10)
                for link in active_links:
                    if not link.is_revoked:
                        await bot.revoke_chat_invite_link(chat_id=channel, invite_link=link.invite_link)
                        logging.info(f"Revoked existing link for {channel}: {link.invite_link}")
            except Exception as e:
                logging.warning(f"Could not fetch/revoke old links for {channel}: {e}")

            # Create new invite link
            invite = await bot.create_chat_invite_link(chat_id=channel, creates_join_request=False)
            last_links[channel] = invite.invite_link

            # Send stylish message to admin
            await bot.send_message(
                chat_id=ADMIN_ID,
                text=f"""✅ *New Invite Link Generated!*

*📢 Channel:* `{channel}`
*🔗 Link:* [Join Now]({invite.invite_link})

⏱️ Auto-refresh every *10 minutes*
♻️ All previous links revoked

🔒 _Secure & Automated by InviteLinkBot™_""",
                parse_mode="Markdown",
                disable_web_page_preview=True
            )

        except Exception as e:
            logging.error(f"Error with {channel}: {e}")
            await bot.send_message(
                chat_id=ADMIN_ID,
                text=f"❌ Error with `{channel}`:\n`{e}`",
                parse_mode="Markdown"
            )

# Main function to run bot
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Start the scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(generate_links, "interval", minutes=1, args=[app])
    scheduler.start()

    # Send startup message to admin
    await app.bot.send_message(
        chat_id=ADMIN_ID,
        text="""✅ *InviteLinkBot™ is now active!*

🔁 Invite links will be refreshed every *10 minutes*
📩 You will get updated links here automatically.

🔒 Sit back and relax!""",
        parse_mode="Markdown"
    )

    logging.info("🚀 Bot is running and scheduler started...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()

# Run main
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
