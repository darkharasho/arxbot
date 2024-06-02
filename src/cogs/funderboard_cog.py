import pdb

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


async def calculate_leaderboard(name, data, guild_id=int):
    members = list(set([api_key.member for api_key in ApiKey.select().where(ApiKey.guild_id == guild_id)]))
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
        showindex=index,
        maxcolwidths=[23, 23, None]
    )

    return table


class FunderboardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = SqliteDatabase('arxbot.db')

    @app_commands.command(
        name="funderboard",
        description="Fun Leaderboard Stats"
    )
    async def funderboard(self, interaction):
        await interaction.response.defer()
        spike_table =  await calculate_leaderboard("Spikes", "legendary_spikes", guild_id=interaction.guild.id)
        supply_table = await calculate_leaderboard("Supply", "weekly_supply_spent", guild_id=interaction.guild.id)
        yak_table =    await calculate_leaderboard("Yaks", "weekly_yaks_escorted", guild_id=interaction.guild.id)

        embed = discord.Embed(
            title="🎉 Funderboard",
            description=f"〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️"
                        f"**🏆 Legendary Spikes:**```{spike_table}```\n"
                        f"**📦 Weekly Repair Masters:**```{supply_table}```\n"
                        f"**🐄 Weekly Yak Escorts:**```{yak_table}```\n"
        )

        await interaction.followup.send(embed=embed)


async def setup(bot):
    for guild in bot.guilds:
        await bot.add_cog(FunderboardCog(bot), guild=guild, override=True)
