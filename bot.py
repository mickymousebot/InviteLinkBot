import os
import logging
import asyncio
from datetime import datetime
import pytz
from telegram import Bot
from telegram.error import TelegramError
from aiohttp import web

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
ADMIN_ID = os.getenv('TELEGRAM_ADMIN_ID')
TIMEZONE = pytz.timezone('Asia/Kolkata')
PORT = int(os.getenv('PORT', 8080))

# Initialize bot and app
bot = Bot(token=TELEGRAM_BOT_TOKEN)
app = web.Application()
routes = web.RouteTableDef()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

@routes.get('/')
async def health_check(request):
    return web.Response(text="Bot is running")

async def generate_new_link():
    try:
        # Revoke all existing links first
        revoked_link = await bot.export_chat_invite_link(chat_id=CHANNEL_ID)
        logger.info(f"Revoked previous link: {revoked_link}")
        
        # Generate new invite link
        new_link = await bot.export_chat_invite_link(chat_id=CHANNEL_ID)
        logger.info(f"Generated new link: {new_link}")
        
        # Log the change with timestamp
        current_time = datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')
        with open('link_logs.txt', 'a') as f:
            f.write(f"{current_time} - {new_link}\n")
            
        # Notify admin
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🔑 New channel link generated at {current_time}:\n{new_link}"
        )
        
    except TelegramError as e:
        logger.error(f"Error in link generation: {e}")
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"⚠️ Error in link generation: {e}"
        )
    finally:
        # Schedule the next execution
        await asyncio.sleep(60)
        asyncio.create_task(generate_new_link())

async def start_background_tasks(app):
    app['bot_task'] = asyncio.create_task(generate_new_link())

async def cleanup_background_tasks(app):
    app['bot_task'].cancel()
    await app['bot_task']

app.add_routes(routes)
app.on_startup.append(start_background_tasks)
app.on_cleanup.append(cleanup_background_tasks)

if __name__ == '__main__':
    logger.info("Starting Telegram Link Revocation Bot")
    web.run_app(app, port=PORT)
