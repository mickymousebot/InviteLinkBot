import os
import logging
import asyncio
from datetime import datetime
import pytz
from telegram import Bot
from telegram.error import TelegramError, BadRequest

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')  # Must include -100 prefix
ADMIN_ID = os.getenv('TELEGRAM_ADMIN_ID')
TIMEZONE = pytz.timezone('Asia/Kolkata')

# Initialize bot
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def check_bot_permissions():
    """Verify bot has proper admin rights"""
    try:
        chat = await bot.get_chat(chat_id=CHANNEL_ID)
        if not chat.permissions.can_invite_users:
            raise PermissionError("Bot lacks invite permissions")
        return True
    except BadRequest as e:
        logger.error(f"Channel access error: {e}")
        raise
    except Exception as e:
        logger.error(f"Permission check failed: {e}")
        raise

async def rotate_link():
    """Generate and revoke links with enhanced error handling"""
    try:
        await check_bot_permissions()
        
        # Revoke old link
        revoked_link = await bot.export_chat_invite_link(chat_id=CHANNEL_ID)
        logger.info(f"Revoked: {revoked_link}")
        
        # Create new link
        new_link = await bot.export_chat_invite_link(chat_id=CHANNEL_ID)
        logger.info(f"New link: {new_link}")
        
        # Log and notify
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🔄 New Link: {new_link}\n⏰ {datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')}"
        )
        return True
        
    except BadRequest as e:
        error_msg = f"⚠️ API Error: {e.message}"
        logger.error(error_msg)
    except TelegramError as e:
        error_msg = f"⚠️ Telegram Error: {str(e)}"
        logger.error(error_msg)
    except Exception as e:
        error_msg = f"⚠️ Unexpected Error: {str(e)}"
        logger.error(error_msg)
    
    await bot.send_message(
        chat_id=ADMIN_ID,
        text=error_msg
    )
    return False

async def main():
    # Startup notification
    await bot.send_message(
        chat_id=ADMIN_ID,
        text="🤖 Bot Starting...\n"
             "🔍 Checking permissions..."
    )
    
    # Permission verification
    try:
        await check_bot_permissions()
        await bot.send_message(
            chat_id=ADMIN_ID,
            text="✅ Bot has correct permissions!\n"
                 "⏳ Starting link rotation..."
        )
    except Exception as e:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"❌ FATAL: {str(e)}\n"
                 "Please make bot admin with invite permissions!"
        )
        return
    
    # Main rotation loop
    while True:
        success = await rotate_link()
        delay = 30 if not success else 60  # Shorter delay on errors
        await asyncio.sleep(delay)

if __name__ == '__main__':
    logger.info("Starting Enhanced Link Rotator")
    asyncio.run(main())
