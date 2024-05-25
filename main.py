import pdb

import discord
import os
from discord.ext import commands
from discord import app_commands
from peewee import *
from config import settings
from src.models.guild import Guild
from src.models.member import Member
from src.models.api_key import ApiKey

# Intents are required for some of the features
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# Create a bot instance with the command prefix "!" and the specified intents
bot = commands.Bot(command_prefix="!", intents=intents, application_id=settings.APPLICATION_ID)
intents = discord.Intents.default()

# Event handler for when the bot is ready
@bot.event
async def on_ready():
    await load_db()
    await load_cogs(cog_type="cogs")
    await load_cogs(cog_type="tasks")
    print(f'Bot is ready. Logged in as {bot.user}')
    print('Connected to the following guilds:')
    for guild in bot.guilds:
        print(f'- {guild.name} (ID: {guild.id})')

async def load_db():
    db = SqliteDatabase('arxbot.db')
    try:
        db.connect()
        db.create_tables([Guild, ApiKey, Member])
        print("[DATABASE]".ljust(20) + f"🟢 DB Connected")
        print("[DATABASE]".ljust(20) + f"🟢 DB Ready")
    except Exception as e:
        print("[DATABASE]".ljust(20) + f"🔴 FAILED")
        if os.getenv('LOG_LEVEL') == "debug":
            raise e
        else:
            print(" ".ljust(23) + f"[ERR] {e}")
            pass

async def load_cogs(cog_type=None):
    if not cog_type:
        raise "Cog Type required"
    print("--------------------------------------------")
    # Load Cog Extensions
    for f in os.listdir(f"./src/{cog_type}"):
        cog = f[:-3]
        if f.endswith(".py"):
            cmd = re.sub(r'_', '-', cog[:-4])
            try:
                await bot.load_extension(f"src.{cog_type}." + cog)
                if cmd in Config.disabled_modules():
                    tree.remove_command(cmd, guild=discord.Object(id=settings.GUILD_ID))
                    print(f"[DISABLED]".ljust(20) + f"🟡 {cog_type}." + cog)
                else:
                    print(f"[{cog_type.upper()} LOADED]".ljust(20) + f"🟢 {cog_type}." + cog)
            except Exception as e:
                print(f"[{cog_type.upper()} FAILED]".ljust(20) + f"🔴 {cog_type}." + cog)
                if os.getenv('LOG_LEVEL') == "debug":
                    raise e
                else:
                    print(" ".ljust(23) + f"[ERR] {e}")

# Command to test if the bot is working
@bot.command(name='ping')
async def ping(ctx):
    await ctx.send('Pong!')

# Event handler for when the bot joins a new guild
@bot.event
async def on_guild_join(guild):
    print(f'Joined new guild: {guild.name} (ID: {guild.id})')
    channel = guild.system_channel
    if channel:
        await channel.send("Hello! Thank you for inviting me to your server!")
    if not Guild.select().where(Guild.guild_id == guild.id).first():
        guild = Guild.create(name=guild.name, guild_id=guild.id)
        guild.save()


# Event handler for when the bot is removed from a guild
@bot.event
async def on_guild_remove(guild):
    print(f'Removed from guild: {guild.name} (ID: {guild.id})')

# Start the bot with your token
bot.run(settings.TOKEN)
