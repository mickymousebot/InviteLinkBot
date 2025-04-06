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
TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID"))  # e.g. -1001234567890
MESSAGE_ID = int(os.getenv("MESSAGE_ID"))  # Message ID to edit

# Logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Load channels list
with open("channels.json", "r") as file:
    CHANNELS = json.load(file)

# Unique emojis for each channel
EMOJIS = ["👿", "♥️", "👻", "⚡", "🤡", "🍫", "🎯", "🌟", "💥", "🔥"]

# Store last invite links
last_links = {}

# Function to generate new links
async def generate_links(app):
    bot = app.bot
    global last_links

    updated_text = "Our Official Channels/Group 👻\n\n"

    for idx, channel in enumerate(CHANNELS):
        emoji = EMOJIS[idx % len(EMOJIS)]
        try:
            # Revoke previous link
            if channel in last_links:
                try:
                    await bot.revoke_chat_invite_link(chat_id=channel, invite_link=last_links[channel])
                    logging.info(f"Revoked old link for {channel}")
                except Exception as e:
                    logging.warning(f"Could not revoke old link for {channel}: {e}")

            # Create new invite link
            invite = await bot.create_chat_invite_link(chat_id=channel, creates_join_request=False)
            last_links[channel] = invite.invite_link

            # Get channel title
            chat_info = await bot.get_chat(channel)
            title = chat_info.title or "Unnamed"

            # Add to update text with HTML formatting — emoji after name
            updated_text += f'▸ <a href="{invite.invite_link}"><i>{title}</i></a> {emoji}\n'

            # Notify admin
            await bot.send_message(
                chat_id=ADMIN_ID,
                text=f"""✅ <b>New Invite Link Generated!</b>

<b>📢 Channel:</b> <code>{channel}</code>
<b>🔗 Link:</b> <a href="{invite.invite_link}">Join Now</a>

⏱️ Auto-refresh every <b>10 minutes</b>
♻️ Old link revoked successfully

🔒 <i>Secure & Automated by InviteLinkBot™</i>""",
                parse_mode="HTML",
                disable_web_page_preview=True
            )

        except Exception as e:
            logging.error(f"Error with {channel}: {e}")
            await bot.send_message(
                chat_id=ADMIN_ID,
                text=f"❌ Error with <code>{channel}</code>:\n<code>{e}</code>",
                parse_mode="HTML"
            )

    # Update pinned channel message
    try:
        await bot.edit_message_text(
            chat_id=TARGET_CHANNEL_ID,
            message_id=MESSAGE_ID,
            text=updated_text,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        logging.info("✅ Channel message updated with new invite links.")
    except Exception as e:
        logging.error(f"❌ Failed to update channel message: {e}")
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"❌ Could not update message:\n<code>{e}</code>",
            parse_mode="HTML"
        )

# Bot main function
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Start scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(generate_links, "interval", minutes=1, args=[app])  # 10 minutes interval
    scheduler.start()

    await app.bot.send_message(
        chat_id=ADMIN_ID,
        text="""✅ <b>InviteLinkBot™ is now active!</b>

🔁 Invite links will be refreshed every <b>10 minutes</b>
📩 You will get updated links here automatically.

🔒 <i>Sit back and relax!</i>
""",
        parse_mode="HTML"
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
