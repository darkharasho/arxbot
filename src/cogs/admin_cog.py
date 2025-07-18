import pdb
import discord
import json
import textwrap
import asyncio

from collections import defaultdict
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
from src.gw2_api_client import GW2ApiClient

tabulate.PRESERVE_WHITESPACE = True


async def send_large_message(interaction, content, chunk_size=2000, ephemeral=True):
    """Utility function to send large messages split into chunks."""
    chunks = textwrap.wrap(content, width=chunk_size, replace_whitespace=False)
    for chunk in chunks:
        await interaction.followup.send(chunk, ephemeral=ephemeral)

class AdminCog(commands.Cog):
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
        description="Admin: Master Commands"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name='Members Without API Keys', value='without_key'),
        app_commands.Choice(name='In Game Members without an API Key', value='gw2_map_without_key'),
    ])
    async def admin(self, interaction: discord.Interaction, action: str):
        if await authorization.ensure_admin(interaction):
            if action == 'without_key':
                # Defer the response to allow time for processing
                await interaction.response.defer()

                try:
                    # Get the guild ID from the interaction
                    guild_id = interaction.guild.id

                    # Fetch all members for the current guild
                    all_members = Member.select().where(Member.guild_id == guild_id)

                    # Dictionary to hold roles and corresponding members
                    roles_to_members = defaultdict(list)
                    excluded_roles = {"Guild Leader", "Guild Officer",
                                      "Server Booster"}

                    # Iterate over all members and filter those without API keys and with the "Alliance Member" role
                    guild = interaction.guild
                    for member in all_members:
                        discord_member = guild.get_member(member.discord_id)
                        if discord_member and discord.utils.get(discord_member.roles, name="Alliance Member"):
                            api_keys = ApiKey.select().where(ApiKey.member == member)
                            if api_keys.count() == 0:
                                for role in discord_member.roles:
                                    if role.name not in excluded_roles and role != guild.default_role:
                                        roles_to_members[role.name].append(member.username)

                    # Prepare the message chunks
                    message_chunks = []
                    current_chunk = []
                    current_length = 0
                    chunk_size = 2000

                    for role, members in roles_to_members.items():
                        role_header = f"**{role}**\n"
                        role_members = "```" + "\n".join(members) + "```"
                        section = role_header + role_members
                        section_length = len(section)

                        if current_length + section_length > chunk_size:
                            message_chunks.append("".join(current_chunk))
                            current_chunk = [section]
                            current_length = section_length
                        else:
                            current_chunk.append(section)
                            current_length += section_length

                    if current_chunk:
                        message_chunks.append("".join(current_chunk))

                    # Send the message chunks
                    for chunk in message_chunks:
                        await interaction.followup.send(chunk)

                except Exception as e:
                    logger.error(f"An error occurred: {e}")
                    await interaction.followup.send(f"An error occurred: {e}")
            if action == 'gw2_map_without_key':
                await interaction.response.defer()
                current_user = Member.select().where(Member.discord_id == interaction.user.id).first()

                if current_user:
                    guild_members = GW2ApiClient(api_key=current_user.api_key).guild_members(
                        gw2_guild_id="23B352FB-9C18-EF11-81A9-8FB5CFBE7766")
                    extra_guild_member_igns = []
                    for member in guild_members:
                        keys = ApiKey.select().where(
                            (ApiKey.guild_id == interaction.guild.id) & (ApiKey.name == member["name"]))
                        if keys.count() == 0:
                            extra_guild_member_igns.append(member["name"])

                    # Prepare the message content
                    member_names_str = "\n".join(extra_guild_member_igns)
                    overall_count_message = f"In Game Guild Members Without API Keys Count: {len(extra_guild_member_igns)}\n"
                    full_message = overall_count_message + member_names_str

                    # Send the large message split into chunks
                    await send_large_message(interaction, full_message, ephemeral=False)

    @app_commands.command(
        name="list_role_gw2",
        description="List all users with a specified Discord role and their GW2 usernames"
    )
    @app_commands.describe(role_name="The name of the Discord role to search for")
    async def list_role_gw2(self, interaction: discord.Interaction, role_name: str):
        await interaction.response.defer()
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            await interaction.followup.send(f"Role '{role_name}' not found.", ephemeral=True)
            return

        members_with_role = [m for m in guild.members if role in m.roles]
        lines = []
        for discord_member in members_with_role:
            db_member = Member.select().where(Member.discord_id == discord_member.id).first()
            gw2_username = db_member.gw2_username if db_member and db_member.gw2_username else "N/A"
            lines.append(f"{discord_member.display_name}: {gw2_username}")

        if not lines:
            await interaction.followup.send(f"No users found with role '{role_name}'.", ephemeral=True)
        else:
            message = "**Users with role '{}':**\n```{}```".format(role_name, "\n".join(lines))
            await interaction.followup.send(message, ephemeral=True)

async def setup(bot):
    for guild in bot.guilds:
        await bot.add_cog(AdminCog(bot), guild=guild, override=True)
