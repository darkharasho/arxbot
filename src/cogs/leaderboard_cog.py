import discord

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


async def calculate_leaderboard(name, data, guild):
    # Optimize query to fetch only required fields and related members
    query = (
        ApiKey.select(ApiKey.member, Member.username, Member.guild_wars_2_name)
        .join(Member)
        .where((ApiKey.guild_id == guild.id) & (ApiKey.leaderboard_enabled == True))
    )

    leaderboard = []
    for api_key in query:
        member = api_key.member
        try:
            # Fetch the required data dynamically
            leaderboard.append([member.username, member.guild_wars_2_name, getattr(member, data)()])
        except Exception as e:
            print(f"Skipping {member.username} due to error: {e}")
            continue  # Gracefully skip this iteration

    # Sort and limit results directly in Python
    sorted_leaderboard = sorted(leaderboard, key=lambda x: x[2], reverse=True)[:settings.MAX_LEADERBOARD_MEMBERS]
    index = range(1, len(sorted_leaderboard) + 1)

    # Generate the table
    headers = ["Name", "GW2 Username", f"{name}"]
    table = tabulate(sorted_leaderboard, headers, tablefmt="simple", showindex=index)

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
