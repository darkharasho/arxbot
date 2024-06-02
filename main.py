import pdb

import discord
import os
import re
import datetime

from discord.ext import commands
from discord import app_commands
from peewee import *
from config import settings
from src.models.guild import Guild
from src.models.member import Member
from src.models.api_key import ApiKey
from src.models.config import Config

import sys
import logging

logger = logging.getLogger('')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('arxbot.log')
sh = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s [%(filename)s.%(funcName)s:%(lineno)d] %(message)s', datefmt='%a, %d %b %Y %H:%M:%S')
fh.setFormatter(formatter)
sh.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(sh)

# Intents are required for some of the features
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True

# Create a bot instance with the command prefix "!" and the specified intents
bot = commands.Bot(command_prefix="!", intents=intents, application_id=settings.APPLICATION_ID)
intents = discord.Intents.default()


# Event handler for when the bot is ready
@bot.event
async def on_ready():
    await load_db()
    await load_cogs(cog_type="cogs")
    await load_cogs(cog_type="tasks")
    await load_views()
    logger.info("--------------------------------------------")
    for guild in bot.guilds:
        logger.info(f'- {guild.name} (ID: {guild.id})')
        await bot.tree.sync(guild=guild)
    logger.info("[FINISH]".ljust(20) + f"♾️ All Commands Loaded")
    logger.info(f'Bot is ready. Logged in as {bot.user}')


async def load_db():
    db = SqliteDatabase('arxbot.db')
    try:
        db.connect()
        logger.info("[DATABASE]".ljust(20) + f"🟢 DB Connected")
        db.create_tables([Guild, ApiKey, Member, Config])
        logger.info("[DATABASE]".ljust(20) + f"🟢 DB Ready")
    except Exception as e:
        logger.critical("[DATABASE]".ljust(20) + f"🔴 FAILED")
        if os.getenv('LOG_LEVEL') == "debug":
            raise e
        else:
            logger.critical(" ".ljust(23) + f"[ERR] {e}")
            pass


async def load_cogs(cog_type=None):
    if not cog_type:
        raise "Cog Type required"
    logger.info("--------------------------------------------")
    # Load Cog Extensions
    for f in os.listdir(f"./src/{cog_type}"):
        cog = f[:-3]
        if f.endswith(".py"):
            cmd = re.sub(r'_', '-', cog[:-4])
            try:
                await bot.load_extension(f"src.{cog_type}." + cog)
                logger.info(f"[{cog_type.upper()} LOADED]".ljust(20) + f"🟢 {cog_type}." + cog)
            except Exception as e:
                logger.warning(f"[{cog_type.upper()} FAILED]".ljust(20) + f"🔴 {cog_type}." + cog)
                if os.getenv('LOG_LEVEL') == "debug":
                    raise e
                else:
                    logger.critical(" ".ljust(23) + f"[ERR] {e}")


async def load_views():
    logger.info("--------------------------------------------")
    for f in os.listdir("./src/views"):
        view = f[:-3]
        if f.endswith(".py"):
            try:
                logger.info("[VIEW LOADED]".ljust(20) + f"🟢 views." + view)
            except Exception as e:
                logger.warning("[VIEW FAILED]".ljust(20) + f"🔴 views." + view)
                if os.getenv('LOG_LEVEL') == "debug":
                    raise e
                else:
                    logger.critical(" ".ljust(23) + f"[ERR] {e}")


# Command to test if the bot is working
@bot.command(name='ping')
async def ping(ctx):
    await ctx.send('Pong!')


# Event handler for when the bot joins a new guild
@bot.event
async def on_guild_join(guild):
    logger.info(f'Joined new guild: {guild.name} (ID: {guild.id})')
    channel = guild.system_channel
    if channel:
        await channel.send("Hello! Thank you for inviting me to your server!")
    if not Guild.select().where(Guild.id == guild.id).first():
        guild = Guild.create(name=guild.name, id=guild.id)
        guild.save()
    await bot.tree.sync(guild=guild)


# Event handler for when the bot is removed from a guild
@bot.event
async def on_guild_remove(guild):
    logger.info(f'Removed from guild: {guild.name} (ID: {guild.id})')


# Start the bot with your token
bot.run(settings.TOKEN)
