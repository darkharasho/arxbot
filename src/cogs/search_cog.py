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
from src.models.api_key import ApiKey
from src.cogs.stats_cog import StatsCog
from datetime import datetime
from src.db_viewer import DBViewer
from src.lib.smart_embed import SmartEmbed

tabulate.PRESERVE_WHITESPACE = True


class SearchCog(commands.Cog):
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
        name="search",
        description="Admin: Tie Discord and Guild Wars 2 data together"
    )
    async def search(self, interaction: discord.Interaction, gw2_account_name: str):
        if await authorization.ensure_admin(interaction):
            await interaction.response.defer(ephemeral=True)

            try:
                # Perform the SQL lookup
                results = ApiKey.select().where(ApiKey.name.contains(gw2_account_name))

                if results:
                    for api_key in results:
                        member = interaction.guild.get_member(api_key.member.discord_id)
                        embed = discord.Embed(title=f"{member.display_name} | {member.name}", description="")
                        embed.set_thumbnail(url=member.display_avatar.url)
                        embed.add_field(name="", value="```------ Accounts ------```", inline=False)
                        embed.add_field(name="", value=f"```" +
                                                       "\n".join(apik.name for apik in api_key.member.api_keys)
                                                       + "```", inline=False)
                        embed.add_field(name="", value="```------ Character Details ------```", inline=False)
                        embed.add_field(name="Characters", value="```" +
                                                                 "\n".join(char for char in api_key.member.characters())
                                                                 + "```", inline=False)
                else:
                    embed = discord.Embed(title="No results found.")

                await interaction.followup.send(embed=embed, ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)


async def setup(bot):
    for guild in bot.guilds:
        await bot.add_cog(SearchCog(bot), guild=guild, override=True)
