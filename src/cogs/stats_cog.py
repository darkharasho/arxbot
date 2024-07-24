import pdb

import discord
import asyncio

from discord.ext import commands
from discord import app_commands
from discord import SelectMenu, SelectOption
from config import settings
from src.gw2_api_client import GW2ApiClient
from src.tasks.stat_updater_task import StatUpdaterTask
from peewee import *
from src.models.member import Member
from src.models.api_key import ApiKey


class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = SqliteDatabase('arxbot.db')

    @app_commands.command(
        name="stats",
        description="See stats about yourself"
    )
    async def stats(self, interaction):
        await self.get_stats(interaction, interaction.user)

    async def get_stats(self, interaction, member):
        await interaction.response.defer(ephemeral=True)
        db_member = Member.find_or_create(member, guild=interaction.guild)

        if db_member.api_key:
            api_client = GW2ApiClient(api_key=db_member.api_key)
            gw2_account_info = api_client.account()

            embed = discord.Embed(
                title="Guild Wars 2 - Weekly Stats",
                description=f"",
                color=member.top_role.color)
            embed.set_thumbnail(url=member.display_avatar.url)

            embed.add_field(name="", value="```------ Account Details ------```", inline=False)
            embed.add_field(name="Guilds", value=f"```" + '\n'.join(db_member.gw2_guild_names()) + "```", inline=False)

            embed.add_field(name="", value="```----- Guild Wars 2 Stats -----```", inline=False)
            if db_member.api_key_is_leaderboard_enabled():
                embed.add_field(name="Accounts", value=f"```" + str(len(db_member.api_keys)) + "```")
                embed.add_field(name="WvW Rank", value=f"```" + str(gw2_account_info["wvw"]["rank"]) + "```")
                embed.add_field(name="Legendary Spikes", value=f"```" + str(db_member.legendary_spikes()) + "```")
                embed.add_field(name="Weekly Ranks", value=f"```" + str(db_member.weekly_ranks_count()) + "```")
                embed.add_field(name="Weekly Kills", value=f"```" + str(db_member.weekly_kill_count()) + "```")
                embed.add_field(name="Weekly Deaths", value=f"```" + str(db_member.weekly_deaths_count()) + "```")
                embed.add_field(name="Weekly KDR", value=f"```" + str(db_member.weekly_kdr()) + "```")
                embed.add_field(name="Weekly Captures", value=f"```" + str(db_member.weekly_capture_count()) + "```")
                embed.add_field(name="", value=f"")
                embed.add_field(name="", value=f"")
            else:
                embed.add_field(name="", value="Your api key does not have sufficient permissions to view personal stats.\nIf you would like to see your stats, please remove the current key with `/remove-key` and add one with additional permissions.")
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="No API Key Found",
                    description=f"A GW2 API key is required to use this command. Register one with `/set-key`",
                    color=0xff0000
                )
            )


async def setup(bot):
    for guild in bot.guilds:
        await bot.add_cog(StatsCog(bot), guild=guild, override=True)
