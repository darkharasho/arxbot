import pdb

import discord
import requests
from datetime import datetime, timedelta, timezone
from discord.ext import commands, tasks
from config import settings
from src.lib.logger import logger
from src.models.config import Config
from src import helpers


class CleanChannelTask(commands.Cog):
    def __init__(self, bot, api_key=None):
        self.bot = bot
        self.clean_channel.start()

    def cog_unload(self):
        self.clean_channel.cancel()

    @tasks.loop(hours=24)
    async def clean_channel(self):
        await self.delete_messages()

    async def delete_messages(self):
        for guild in self.bot.guilds:
            clean_channel_config = Config.clean_channel(guild_id=guild.id)
            if not clean_channel_config:
                continue
            if not helpers.str_to_bool(clean_channel_config["enabled"]):
                continue

            channel = self.bot.get_channel(clean_channel_config['channel_id'])
            if not channel:
                logger.info(f"Channel with ID {clean_channel_config['channel_id']} not found.")
                continue

            now = datetime.now(timezone.utc)
            one_week_ago = now - timedelta(days=7)
            two_weeks_ago = now - timedelta(days=14)

            # Purge messages younger than 14 days and older than 7 days
            try:
                await channel.purge(before=one_week_ago, after=two_weeks_ago)
                logger.debug(f"Purged messages in channel {channel.id}")
            except Exception as e:
                logger.debug(f"Failed to purge messages in channel {channel.id}: {e}")

            # Delete messages older than 14 days individually
            async for message in channel.history(limit=None, before=two_weeks_ago):
                if message.created_at < one_week_ago:
                    try:
                        await message.delete()
                        logger.debug(f"Deleted message from {message.author} sent at {message.created_at}")
                    except Exception as e:
                        logger.debug(f"Failed to delete message from {message.author}: {e}")


async def setup(bot):
    for guild in bot.guilds:
        await bot.add_cog(CleanChannelTask(bot), guild=guild, override=True)
