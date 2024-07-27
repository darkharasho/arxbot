import pdb
import discord
import json

from discord.ext import commands
from discord import app_commands
from config import settings
from src import helpers
from src import authorization
from tabulate import tabulate
from src.gw2_api_client import GW2ApiClient
from peewee import *
from src.models.member import Member
from src.cogs.stats_cog import StatsCog
from datetime import datetime
from src.db_viewer import DBViewer
from src.lib.smart_embed import SmartEmbed

tabulate.PRESERVE_WHITESPACE = True


class AdminLookup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def model_to_dict(self, model):
        """Convert a Peewee model instance to a dictionary."""
        return {
            'value': model.value,
            'name': model.name,
            'primary': model.primary
        }

    @app_commands.command(
        name="admin_lookup",
        description="Admin: Tie Discord and Guild Wars 2 data together"
    )
    async def admin_lookup(self, interaction: discord.Interaction, member: discord.Member):
        if await authorization.ensure_admin(interaction):
            await interaction.response.defer(ephemeral=True)
            db_member = Member.find_or_create(member=member, guild=interaction.guild)

            embed = discord.Embed(title=f"{member.display_name} | {member.name}", description="")
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="", value="```------ Account Details ------```", inline=False)

            if len(db_member.api_keys) > 0:
                embed.add_field(name="Guilds", value=f"```- " + '\n- '.join(db_member.gw2_guild_names()) + "```",
                                inline=False)
                embed.add_field(name="GW2 Accounts", value="```- " + "\n- ".join(api_key.name for api_key in db_member.api_keys) + "```", inline=False)
            else:
                embed.add_field(name="API Keys", value="```No API Keys found```", inline=False)
            await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    for guild in bot.guilds:
        await bot.add_cog(AdminLookup(bot), guild=guild, override=True)
