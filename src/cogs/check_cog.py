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

tabulate.PRESERVE_WHITESPACE = True


class CheckCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def model_to_dict(self, model):
        """Convert a Peewee model instance to a dictionary."""
        return {
            'id': model.id,
            'value': model.value,
            'name': model.name,
            'primary': model.primary
        }

    @app_commands.command(
        name="check",
        description="Admin: Debug Member"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name='📈 Stats', value='stats'),
        app_commands.Choice(name='🔎 DB Details', value='db_details')
    ])
    async def check(self, interaction: discord.Interaction, member: discord.Member, action: str):
        if await authorization.ensure_admin(interaction):
            if action == 'stats':
                await StatsCog(self.bot).get_stats(interaction, member)
            elif action == 'db_details':
                await interaction.response.defer(ephemeral=True)

                db_member = Member.select().where(
                    (Member.discord_id == member.id) & (Member.guild_id == interaction.guild.id)).first()

                # Convert api_keys to a list of dictionaries
                api_keys = [self.model_to_dict(api_key) for api_key in db_member.api_keys]

                db_member_dict = {
                    'ID': db_member.id,
                    'Username': db_member.username,
                    'Created At': db_member.created_at,
                    'Updated At': db_member.updated_at,
                    'GuildID': db_member.guild_id,
                    'DiscordID': db_member.discord_id,
                    'GW2 API Key': api_keys,  # Use the list of dictionaries
                    'GW2 Stats': db_member.gw2_stats if db_member.gw2_stats else {}
                }

                embed = discord.Embed(title=f"Database Details for {db_member.username}", description="")
                embed.add_field(name="API Keys", value=str(len(api_keys)), inline=True)
                embed.add_field(name="Member Since", value=db_member.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                                inline=True)

                role_mentions = ' '.join(
                    [role.mention for role in member.roles if role != interaction.guild.default_role])
                embed.add_field(name="Roles", value=role_mentions if role_mentions else "No roles assigned",
                                inline=False)

                # Add the formatted JSON
                pretty_json = json.dumps(db_member_dict, indent=4, sort_keys=True, default=str)
                embed.add_field(name="Details", value=f"```json\n{pretty_json}```", inline=False)

                await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    for guild in bot.guilds:
        await bot.add_cog(CheckCog(bot), guild=guild, override=True)
