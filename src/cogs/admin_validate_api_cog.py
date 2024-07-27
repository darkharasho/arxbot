import pdb
import discord
import json

from discord.ext import commands
from discord import app_commands
from config import settings
from src import helpers
from src.lib.logger import logger
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

                try:
                    # Raw SQL query to find members without API keys
                    sql_query = """
                        SELECT member.id, member.username, member.discord_id
                        FROM member
                        LEFT JOIN api_key ON member.id = api_key.member_id
                        WHERE api_key.id IS NULL
                    """

                    # Execute raw SQL query
                    members_without_keys = Member.raw(sql_query).execute()

                    # Debug: Print members without API keys
                    logger.info("Debug: Members without API Keys")
                    for member in members_without_keys:
                        logger.info(f"Member: {member.username}, Discord ID: {member.discord_id}")

                    # Create a table using tabulate with multiple members per row
                    rows = []
                    current_row = []
                    max_per_row = 3  # Number of members per row
                    guild = interaction.guild

                    # Filter for members with the "Alliance Member" role
                    for member in members_without_keys:
                        discord_member = guild.get_member(member.discord_id)
                        if discord_member and discord.utils.get(discord_member.roles, name="Alliance Member"):
                            current_row.append(member.username)
                            if len(current_row) == max_per_row:
                                rows.append(current_row)
                                current_row = []

                    # Append any remaining members
                    if current_row:
                        rows.append(current_row)

                    # Convert the rows to a string
                    table_str = tabulate(rows, tablefmt="grid")

                    # Split the table into chunks to fit into multiple embeds
                    MAX_CHAR = 1024
                    table_chunks = [table_str[i:i + MAX_CHAR] for i in range(0, len(table_str), MAX_CHAR)]

                    # Create the embeds
                    embeds = []
                    for i, chunk in enumerate(table_chunks):
                        embed = discord.Embed(title=f"📊 Alliance Members Without API Keys (Page {i + 1})",
                                      description=f"```\n{chunk}\n```")
                        embeds.append(embed)

                    # Send the embeds
                    for embed in embeds:
                        await interaction.followup.send(embed=embed, ephemeral=True)
                except Exception as e:
                    logger.error(f"An error occurred: {e}")
                    print(f"An error occurred: {e}")  # Fallback print to stdout


async def setup(bot):
    for guild in bot.guilds:
        await bot.add_cog(AdminValidateApiCog(bot), guild=guild, override=True)
