import logging
import discord
import asyncio  # Import asyncio to use asyncio.gather

from discord.ext import commands
from discord import app_commands
from config import settings
from src import helpers
from src import authorization
from tabulate import tabulate
from src.gw2_api_client import GW2ApiClient
from peewee import *
from src.models.member import Member
from src.models.api_key import ApiKey
tabulate.PRESERVE_WHITESPACE = True

# Configure the logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)  # Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR)


async def calculate_leaderboard(name, data, guild):
    # Optimize query to fetch only required fields and related members
    query = (
        ApiKey.select(ApiKey.member, Member.username, Member.gw2_username, Member.discord_id, Member.gw2_stats)
        .join(Member)
        .where((ApiKey.guild_id == guild.id))
    )

    leaderboard = {}
    alliance_role = discord.utils.get(guild.roles, name="Alliance Member")  # Get the "Alliance Member" role

    # Create a dictionary of cached members for quick lookup
    cached_members = {member.id: member for member in guild.members}

    for api_key in query:
        member = api_key.member

        # Skip if discord_id is missing
        if not member.discord_id:
            continue

        # Use the cached member instead of fetching from the API
        discord_member = cached_members.get(member.discord_id)
        if not discord_member:
            continue

        # Skip if the Discord member does not have the "Alliance Member" role
        if alliance_role not in discord_member.roles:
            continue

        # Ensure the member has the required attribute or method
        if not hasattr(member, data):
            continue

        try:
            # Fetch the required data dynamically
            value = getattr(member, data)()

            # Truncate GW2 Username to 15 characters
            truncated_gw2_username = member.gw2_username[:15] if member.gw2_username else "Unknown"

            # Add to leaderboard only if the gw2_username is not already present
            if truncated_gw2_username not in leaderboard:
                leaderboard[truncated_gw2_username] = [member.username, truncated_gw2_username, value]
        except Exception:
            continue  # Gracefully skip this iteration

    # Convert the leaderboard dictionary to a list and sort it
    sorted_leaderboard = sorted(leaderboard.values(), key=lambda x: x[2], reverse=True)[:settings.MAX_LEADERBOARD_MEMBERS]
    index = range(1, len(sorted_leaderboard) + 1)

    # Generate the table
    headers = ["Name", "GW2 Username", f"{name}"]
    table = tabulate(
        sorted_leaderboard,
        headers,
        tablefmt="simple",
        showindex=index,
        maxcolwidths=[23, 23, None]
    )

    return table


class LeaderboardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = SqliteDatabase('arxbot.db')

    @app_commands.command(
        name="leaderboard",
        description="Leaderboards for GW2 stats"
    )
    async def leaderboard(self, interaction):
        await interaction.response.defer()

        # Run leaderboard calculations in parallel
        kill_table, kdr_table, capture_table = await asyncio.gather(
            calculate_leaderboard("Kills", "weekly_kill_count", interaction.guild),
            calculate_leaderboard("KDR", "weekly_kdr", interaction.guild),
            calculate_leaderboard("Captures", "weekly_capture_count", interaction.guild),
        )

        # Create and send the embed
        embed = discord.Embed(
            title="📊 Weekly Leaderboard",
            description=f"〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️"
                        f"\n**⚔️ Kills: **```{kill_table}```"
                        f"\n**🧿 KDR:**```{kdr_table}```"
                        f"\n**🏰 Captures:**```{capture_table}```"
        )

        await interaction.followup.send(embed=embed)


async def setup(bot):
    for guild in bot.guilds:
        await bot.add_cog(LeaderboardCog(bot), guild=guild, override=True)
