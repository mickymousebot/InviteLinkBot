import os
import logging
from threading import Timer
from datetime import datetime
import pytz
from telegram import Bot
from telegram.error import TelegramError

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')  # Channel username or ID (prefixed with -100 for IDs)
ADMIN_ID = os.getenv('TELEGRAM_ADMIN_ID')  # Your user ID for error notifications
TIMEZONE = pytz.timezone('Asia/Kolkata')  # Change to your preferred timezone

# Initialize bot
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def generate_new_link():
    try:
        # Revoke all existing links first
        revoked_link = bot.export_chat_invite_link(chat_id=CHANNEL_ID)
        logger.info(f"Revoked previous link: {revoked_link}")
        
        # Generate new invite link
        new_link = bot.export_chat_invite_link(chat_id=CHANNEL_ID)
        logger.info(f"Generated new link: {new_link}")
        
        # Log the change with timestamp
        current_time = datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')
        with open('link_logs.txt', 'a') as f:
            f.write(f"{current_time} - {new_link}\n")
            
        # Notify admin (optional)
        bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🔑 New channel link generated at {current_time}:\n{new_link}"
        )
        
    except TelegramError as e:
        logger.error(f"Error in link generation: {e}")
        bot.send_message(
            chat_id=ADMIN_ID,
            text=f"⚠️ Error in link generation: {e}"
        )
    finally:
        # Schedule the next execution
        Timer(60.0, generate_new_link).start()

if __name__ == '__main__':
    try:
        logger.info("Starting Telegram Link Revocation Bot")
        # Initial call to start the cycle
        generate_new_link()
    except Exception as e:
        logger.critical(f"Bot crashed: {e}")
        bot.send_message(
            chat_id=ADMIN_ID,
            text=f"❌ Bot crashed: {e}"
        )
