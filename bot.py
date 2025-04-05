import os
import logging
import asyncio
from datetime import datetime
import pytz
from telegram import Bot
from telegram.error import TelegramError

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
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

async def rotate_link():
    """Generate new invite link and notify admin"""
    while True:
        try:
            # Revoke existing link and create new one
            revoked_link = await bot.export_chat_invite_link(chat_id=CHANNEL_ID)
            new_link = await bot.export_chat_invite_link(chat_id=CHANNEL_ID)
            
            current_time = datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')
            log_message = f"{current_time} - New: {new_link} | Revoked: {revoked_link}"
            
            logger.info(log_message)
            with open('link_logs.txt', 'a') as f:
                f.write(log_message + "\n")
                
            await bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🔄 Link Rotated\n⏰ {current_time}\n🔗 {new_link}"
            )
            
        except TelegramError as e:
            logger.error(f"Rotation failed: {e}")
            await bot.send_message(
                chat_id=ADMIN_ID,
                text=f"⚠️ Rotation failed: {e}"
            )
            await asyncio.sleep(30)  # Shorter wait if error
            continue
            
        await asyncio.sleep(60)  # Normal 60 second interval

async def main():
    # Send startup notification
    await bot.send_message(
        chat_id=ADMIN_ID,
        text="🤖 Bot Started Successfully!\n"
             "⏳ Beginning link rotation..."
    )
    
    # Start rotation task
    rotation_task = asyncio.create_task(rotate_link())
    
    # Keep the app running
    try:
        while True:
            await asyncio.sleep(3600)  # Sleep for long periods
    except asyncio.CancelledError:
        rotation_task.cancel()
        await rotation_task
        await bot.send_message(
            chat_id=ADMIN_ID,
            text="🛑 Bot Shutting Down!"
        )

if __name__ == '__main__':
    logger.info("Starting Link Rotation Service")
    
    # Koyeb-specific adjustment
    if os.getenv('KOYEB', 'false').lower() == 'true':
        logger.info("Running in Koyeb environment - simplified mode")
        asyncio.run(main())
    else:
        # Original aiohttp code for non-Koyeb deployments
        from aiohttp import web
        app = web.Application()
        
        async def koyeb_handler(request):
            return web.Response(text="OK")
        
        app.router.add_get('/', koyeb_handler)
        
        async def start_bg(app):
            app['bg_task'] = asyncio.create_task(main())
        
        async def cleanup_bg(app):
            app['bg_task'].cancel()
            await app['bg_task']
        
        app.on_startup.append(start_bg)
        app.on_cleanup.append(cleanup_bg)
        
        web.run_app(app, port=int(os.getenv('PORT', 8080)))
