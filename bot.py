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

# Function to revoke all invite links and create a new one
async def generate_links(app):
    bot = app.bot

    for channel in CHANNELS:
        try:
            # 🔥 1. Revoke ALL active invite links
            try:
                invite_links = await bot.get_chat_invite_links(chat_id=channel, creates_join_request=False)
                for inv in invite_links:
                    await bot.revoke_chat_invite_link(chat_id=channel, invite_link=inv.invite_link)
                logging.info(f"✅ Revoked all old links for {channel}")
            except Exception as e:
                logging.warning(f"⚠️ Couldn't revoke all links for {channel}: {e}")

            # ✅ 2. Create fresh link
            invite = await bot.create_chat_invite_link(
                chat_id=channel,
                creates_join_request=False,
                name="AutoLinkBot"
            )

            # ✅ 3. Send new link to all admins
            for admin_id in ADMIN_IDS:
                await bot.send_message(
                    chat_id=admin_id,
                    text=f"""✅ *Fresh Invite Link Generated!*

*📢 Channel:* `{channel}`
*🔗 Link:* [Join Now]({invite.invite_link})

🔥 *All previous links revoked*
🔁 *Auto-refresh every 10 minutes*

🔒 _Powered by InviteLinkBot™_""",
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )

        except Exception as e:
            logging.error(f"❌ Error with {channel}: {e}")
            for admin_id in ADMIN_IDS:
                await bot.send_message(
                    chat_id=admin_id,
                    text=f"❌ Error with `{channel}`:\n`{e}`",
                    parse_mode="Markdown"
                )

# Main function to run bot
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Start the scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(generate_links, "interval", minutes=10, args=[app])
    scheduler.start()

    # Send startup message to all admins
    for admin_id in ADMIN_IDS:
        await app.bot.send_message(
            chat_id=admin_id,
            text="""✅ *InviteLinkBot™ is now active!*

🔁 Invite links will be refreshed every *10 minutes*
📩 You will get updated links here automatically.

🔒 Sit back and relax!
""",
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
