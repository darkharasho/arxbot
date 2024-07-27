import pdb
import discord
import json

from discord.ext import commands
from discord import app_commands
from config import settings
from src import helpers
from src import authorization
from tabulate import tabulate
from peewee import *
from src.models.member import Member
from src.models.api_key import ApiKey
from datetime import datetime
from src.db_viewer import DBViewer
from src.lib.smart_embed import SmartEmbed

tabulate.PRESERVE_WHITESPACE = True


class AdminValidateApiCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def model_to_dict(self, model):
        """Convert a Peewee model instance to a dictionary."""
        return {
            'key': model.value,
            'name': model.name,
            'primary': model.primary
        }

    @app_commands.command(
        name="admin_validate_api",
        description="Admin: Validate members with API keys and those without"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name='📈 Stats', value='stats'),
        app_commands.Choice(name='❌🗝️ Without Key', value='without_key')
    ])
    async def admin_validate_api(self, interaction: discord.Interaction, action: str):
        if await authorization.ensure_admin(interaction):
            if action == 'stats':
                await interaction.response.defer(ephemeral=True)
                # Query members with and without API keys
                mem_with_key = Member.select().join(ApiKey).distinct()
                mem_without_key = Member.select().join(ApiKey, JOIN.LEFT_OUTER).where(ApiKey.id.is_null())

                # Create a table using tabulate
                table = [
                    ["Status", "Count"],
                    ["With Key", len(mem_with_key)],
                    ["Without Key", len(mem_without_key)]
                ]

                # Convert the table to a string
                table_str = tabulate(table, headers="firstrow", tablefmt="grid")

                # Create the embed
                embed = SmartEmbed(title="📊 API Key Stats", description=f"```\n{table_str}\n```")
                embeds = embed.create_embeds()

                # Send the embed
                for embed in embeds:
                    await interaction.followup.send(embed=embed, ephemeral=True)
            elif action == 'without_key':
                # Defer the response to allow time for processing
                await interaction.response.defer(ephemeral=True)

                # Query for members without API keys
                members_without_keys = Member.select().join(ApiKey, JOIN.LEFT_OUTER).where(ApiKey.id.is_null())

                # Debug: Print members without API keys
                print("Debug: Members without API Keys")
                for member in members_without_keys:
                    print(f"Member: {member.username}, Discord ID: {member.discord_id}")

                # Create a table using tabulate
                table = [["Username"]]
                for member in members_without_keys:
                    table.append([member.username])

                # Convert the table to a string
                table_str = tabulate(table, headers="firstrow", tablefmt="grid")

                # Create the embed
                embed = SmartEmbed(title="📊 Members Without API Keys", description=f"```\n{table_str}\n```")
                embeds = embed.create_embeds()

                # Send the embed
                for embed in embeds:
                    await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    for guild in bot.guilds:
        await bot.add_cog(AdminValidateApiCog(bot), guild=guild, override=True)
