import discordi
from discord.ext import commands

# Intents are required for some of the features
intents = discord.Intents.default()
intents.message_content = True

# Create a bot instance with the command prefix "!" and the specified intents
bot = commands.Bot(command_prefix="!", intents=intents)

# Event handler for when the bot is ready
@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')
    print('Connected to the following guilds:')
    for guild in bot.guilds:
        print(f'- {guild.name} (ID: {guild.id})')

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

# Event handler for when the bot is removed from a guild
@bot.event
async def on_guild_remove(guild):
    print(f'Removed from guild: {guild.name} (ID: {guild.id})')

# Start the bot with your token
bot.run('YOUR_BOT_TOKEN')