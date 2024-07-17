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
    members = list(set([api_key.member for api_key in ApiKey.select().where((ApiKey.guild_id == guild_id) & (ApiKey.leaderboard_enabled == True))]))
    leaderboard = []
    for member in members:
        leaderboard.append([member.username, member.gw2_name(), getattr(member, data)()])
    sorted_leaderboard = sorted(leaderboard, key=lambda x: x[2], reverse=True)
    index = [i for i in range(1, len(sorted_leaderboard[:settings.MAX_LEADERBOARD_MEMBERS]) + 1)]

    tablefmt = "simple"
    headers = ["Name", "GW2 Username", f"{name}"]
    table = tabulate(
        sorted_leaderboard[:settings.MAX_LEADERBOARD_MEMBERS],
        headers,
        tablefmt=tablefmt,
        showindex=index
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
        kill_table = await calculate_leaderboard("Kills", "weekly_kill_count", interaction.guild)
        kdr_table = await calculate_leaderboard("KDR", "weekly_kdr", interaction.guild)
        capture_table = await calculate_leaderboard("Captures", "weekly_capture_count", interaction.guild)

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
