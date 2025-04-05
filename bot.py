import os
import logging
from datetime import datetime, timedelta
from threading import Timer
from telegram import Bot, Update, ChatInviteLink
from telegram.ext import Updater, CommandHandler, CallbackContext

# Configuration
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')  # Set this in Koyeb environment variables
CHANNEL_ID = os.getenv('CHANNEL_ID')  # Your private channel ID (negative number)
ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id]  # Comma-separated list of admin user IDs

# Global variables
active_links = {}
bot = Bot(token=BOT_TOKEN)

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def generate_invite_link(context: CallbackContext) -> ChatInviteLink:
    """Generate a new primary invite link for the channel."""
    try:
        # Create a new invite link that expires in 2 minutes (as a safety margin)
        invite_link = bot.create_chat_invite_link(
            chat_id=CHANNEL_ID,
            name="Temporary Access",
            expire_date=datetime.now() + timedelta(minutes=2),
            member_limit=1
        )
        
        logger.info(f"Generated new invite link: {invite_link.invite_link}")
        return invite_link
    except Exception as e:
        logger.error(f"Error generating invite link: {e}")
        raise

def revoke_invite_link(invite_link: str):
    """Revoke an existing invite link."""
    try:
        bot.revoke_chat_invite_link(chat_id=CHANNEL_ID, invite_link=invite_link)
        logger.info(f"Revoked invite link: {invite_link}")
    except Exception as e:
        logger.error(f"Error revoking invite link {invite_link}: {e}")

def start_rotation(context: CallbackContext):
    """Start the invite link rotation process."""
    try:
        # Generate new link
        new_link = generate_invite_link(context)
        
        # Store the active link
        active_links[CHANNEL_ID] = new_link.invite_link
        
        # Schedule revocation after 1 minute
        Timer(60.0, revoke_and_rotate, args=[context]).start()
        
        return new_link.invite_link
    except Exception as e:
        logger.error(f"Error in start_rotation: {e}")
        raise

def revoke_and_rotate(context: CallbackContext):
    """Revoke the current link and start a new rotation."""
    try:
        # Revoke current link if it exists
        current_link = active_links.get(CHANNEL_ID)
        if current_link:
            revoke_invite_link(current_link)
            del active_links[CHANNEL_ID]
        
        # Start new rotation
        start_rotation(context)
    except Exception as e:
        logger.error(f"Error in revoke_and_rotate: {e}")

def start(update: Update, context: CallbackContext):
    """Handler for the /start command."""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        update.message.reply_text("You are not authorized to use this bot.")
        return
    
    try:
        if CHANNEL_ID in active_links:
            # Send existing active link
            update.message.reply_text(
                f"Current active invite link:\n{active_links[CHANNEL_ID]}\n"
                "This link will expire in 1 minute and be replaced automatically."
            )
        else:
            # Start new rotation
            new_link = start_rotation(context)
            update.message.reply_text(
                f"New invite link generated:\n{new_link}\n"
                "This link will expire in 1 minute and be replaced automatically."
            )
    except Exception as e:
        update.message.reply_text("Failed to generate invite link. Please try again.")
        logger.error(f"Error in /start command: {e}")

def main():
    """Start the bot."""
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # Add handlers
    dp.add_handler(CommandHandler("start", start))
    
    # Start the Bot
    updater.start_polling()
    logger.info("Bot started and polling...")
    
    # Start the initial rotation if no active link exists
    if not active_links.get(CHANNEL_ID):
        try:
            start_rotation(dp)
        except Exception as e:
            logger.error(f"Failed to start initial rotation: {e}")
    
    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()
