import pdb

import discord
import requests
from datetime import datetime, timedelta, timezone
from discord.ext import commands, tasks
from config import settings
from src.lib.logger import logger
from src.models.config import Config
from src import helpers


class ReloadCogsTask(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reload_cogs.start()

    def cog_unload(self):
        self.reload_cogs.cancel()

    @tasks.loop(hours=1)
    async def reload_cogs(self):
        logger.info("[COG SYNC]".ljust(20) + f"🟢 STARTED")
        try:
            await self.bot.tree.sync()
            logger.info("[COG SYNC]".ljust(20) + f"🟢 COMPLETE")
        except Exception as e:
            logger.info("[COG SYNC]".ljust(20) + f"🔴 FAILED")
            print(e)


async def setup(bot):
    for guild in bot.guilds:
        await bot.add_cog(ReloadCogsTask(bot), guild=guild, override=True)
