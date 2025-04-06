import os
import json
import logging
from datetime import datetime
from typing import Dict, List
from threading import Event
from dotenv import load_dotenv
from telegram import Bot, Chat, ChatInviteLink
from telegram.ext import Application, ApplicationBuilder

# Load environment variables
load_dotenv()

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
CONFIG_FILE = 'channels.json'
ROTATION_INTERVAL = 600  # 10 minutes in seconds

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class LinkRotatorBot:
    def __init__(self):
        self.bot = Bot(token=BOT_TOKEN)
        self.application = ApplicationBuilder().token(BOT_TOKEN).build()
        self.channels = self._load_channels()
        self.active_links: Dict[str, ChatInviteLink] = {}

    def _load_channels(self) -> List[Dict]:
        """Load channel configurations from JSON file"""
        try:
            with open(CONFIG_FILE, 'r') as f:
                channels = json.load(f)
                if not isinstance(channels, list):
                    raise ValueError("Config file should contain a list of channels")
                return channels
        except FileNotFoundError:
            logger.error(f"Config file {CONFIG_FILE} not found")
            raise
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in config file {CONFIG_FILE}")
            raise
        except Exception as e:
            logger.error(f"Error loading channels: {e}")
            raise

    async def _revoke_link(self, chat_id: str) -> bool:
        """Revoke the current invite link for a channel"""
        try:
            if chat_id in self.active_links:
                link = self.active_links[chat_id]
                await self.bot.revoke_chat_invite_link(chat_id, link.invite_link)
                logger.info(f"Revoked link for channel {chat_id}")
                return True
        except Exception as e:
            logger.error(f"Error revoking link for {chat_id}: {e}")
        return False

    async def _generate_new_link(self, channel: Dict) -> ChatInviteLink:
        """Generate a new invite link for a channel"""
        try:
            chat_id = channel['id']
            name = channel.get('name', chat_id)
            
            # Optional parameters from config
            expire_date = channel.get('expire_date')
            member_limit = channel.get('member_limit')
            
            link = await self.bot.create_chat_invite_link(
                chat_id=chat_id,
                name=f"AutoRotated_{datetime.now().strftime('%Y%m%d%H%M')}",
                expire_date=expire_date,
                member_limit=member_limit,
                creates_join_request=channel.get('join_request', False)
            )
            
            self.active_links[chat_id] = link
            logger.info(f"Generated new link for channel {name} ({chat_id})")
            return link
        except Exception as e:
            logger.error(f"Error generating link for {channel.get('name', chat_id)}: {e}")
            raise

    async def _notify_admin(self, channel: Dict, old_link: str, new_link: str):
        """Send notification to admin about link rotation"""
        try:
            message = (
                f"🔒 *Link Rotation Completed*\n\n"
                f"*Channel:* {channel.get('name', channel['id'])}\n"
                f"*Channel ID:* `{channel['id']}`\n"
                f"*Old Link:* {'Revoked' if old_link else 'None'}\n"
                f"*New Link:* [Click Here]({new_link})\n"
                f"*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            await self.bot.send_message(
                chat_id=ADMIN_ID,
                text=message,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.error(f"Error notifying admin: {e}")

    async def rotate_links(self, context):
        """Main function to rotate links for all channels"""
        logger.info("Starting link rotation cycle")
        
        for channel in self.channels:
            chat_id = channel['id']
            channel_name = channel.get('name', chat_id)
            
            try:
                # Revoke old link
                old_link = self.active_links.get(chat_id)
                await self._revoke_link(chat_id)
                
                # Generate new link
                new_link = await self._generate_new_link(channel)
                
                # Notify admin
                await self._notify_admin(
                    channel,
                    old_link.invite_link if old_link else None,
                    new_link.invite_link
                )
                
            except Exception as e:
                logger.error(f"Failed to rotate link for {channel_name}: {e}")
                try:
                    await self.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=f"❌ *Error rotating link for {channel_name}*\n\nError: {e}",
                        parse_mode='Markdown'
                    )
                except Exception as notify_error:
                    logger.error(f"Failed to send error notification: {notify_error}")

    async def start(self):
        """Start the bot and schedule jobs"""
        logger.info("Starting Link Rotator Bot")
        
        # Schedule the job
        self.application.job_queue.run_repeating(
            self.rotate_links,
            interval=ROTATION_INTERVAL,
            first=10
        )
        
        # Start the bot
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        # Run until stopped
        await self.application.stop()

if __name__ == '__main__':
    try:
        import asyncio
        bot = LinkRotatorBot()
        asyncio.run(bot.start())
    except Exception as e:
        logger.critical(f"Bot failed to start: {e}")
