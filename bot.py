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
TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID"))  # Example: -1001234567890
MESSAGE_ID = int(os.getenv("MESSAGE_ID"))  # Message ID to edit

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

    updated_text = "Our Official Channels/Group 👻\n"

    for channel in CHANNELS:
        try:
            # Revoke old invite link
            if channel in last_links:
                try:
                    await bot.revoke_chat_invite_link(chat_id=channel, invite_link=last_links[channel])
                    logging.info(f"Revoked old link for {channel}")
                except Exception as e:
                    logging.warning(f"Could not revoke old link for {channel}: {e}")

            # Create new invite link
            invite = await bot.create_chat_invite_link(chat_id=channel, creates_join_request=False)
            last_links[channel] = invite.invite_link

            # Add to message update
            chat_info = await bot.get_chat(channel)
            title = chat_info.title or "Unnamed"
            emoji = "👿"  # Default emoji
            updated_text += f"{title} ({invite.invite_link}) {emoji}\n"

            # Send stylish message to admin
            await bot.send_message(
                chat_id=ADMIN_ID,
                text=f"""✅ *New Invite Link Generated!*

*📢 Channel:* `{channel}`
*🔗 Link:* [Join Now]({invite.invite_link})

⏱️ Auto-refresh every *10 minutes*
♻️ Old link revoked successfully

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

    # Update the pinned post in your channel
    try:
        await bot.edit_message_text(
            chat_id=TARGET_CHANNEL_ID,
            message_id=MESSAGE_ID,
            text=updated_text
        )
        logging.info("✅ Channel message updated with new invite links.")
    except Exception as e:
        logging.error(f"❌ Failed to update channel message: {e}")
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"❌ Could not update message:\n`{e}`",
            parse_mode="Markdown"
        )

# Main function
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Start scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(generate_links, "interval", minutes=10, args=[app])
    scheduler.start()

    await app.bot.send_message(
        chat_id=ADMIN_ID,
        text="""
✅ *InviteLinkBot™ is now active!*

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

# Run
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
