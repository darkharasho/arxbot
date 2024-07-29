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


async def send_large_message(interaction, content, chunk_size=2000):
    """Utility function to send large messages split into chunks."""
    chunks = textwrap.wrap(content, width=chunk_size, replace_whitespace=False)
    for chunk in chunks:
        await interaction.followup.send(chunk, ephemeral=True)

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
        app_commands.Choice(name='❌🗝️ Without Key', value='without_key'),
        app_commands.Choice(name='📃 Raw Without Key', value='raw_without_key'),
        app_commands.Choice(name='🛡️ GW2 Map Without Key', value='gw2_map_without_key'),
        app_commands.Choice(name='🛠️ Fix Alliance Member Role', value='without_alliance_member'),
        app_commands.Choice(name='👤 Create Default Users', value='create_default_users'),
        app_commands.Choice(name='🚮 Remove roles without api key', value='remove_roles'),
        app_commands.Choice(name='🔔 Ping', value='ping')
    ])
    async def admin_validate_api(self, interaction: discord.Interaction, action: str):
        if await authorization.ensure_admin(interaction):
            if action == 'stats':
                # Defer the response to allow time for processing
                await interaction.response.defer(ephemeral=True)

                try:
                    # Get the guild ID from the interaction
                    guild_id = interaction.guild.id

                    # Fetch all members for the current guild
                    all_members = Member.select().where(Member.guild_id == guild_id)

                    # Initialize counters
                    members_with_keys_count = 0
                    members_without_keys_count = 0

                    # Initialize sets to track unique members
                    members_with_keys_set = set()
                    members_without_keys_set = set()

                    # Iterate over all members and count those with and without API keys
                    for member in all_members:
                        discord_member = interaction.guild.get_member(member.discord_id)
                        if discord_member and discord.utils.get(discord_member.roles, name="Alliance Member"):
                            api_keys = ApiKey.select().where(ApiKey.member == member)
                            if api_keys.count() > 0:
                                members_with_keys_count += 1
                                members_with_keys_set.add(member.id)
                            else:
                                members_without_keys_count += 1
                                members_without_keys_set.add(member.id)

                    # Create a table using tabulate
                    table = [
                        ["Status", "Count"],
                        ["With Key", members_with_keys_count],
                        ["Without Key", members_without_keys_count]
                    ]

                    # Convert the table to a string
                    table_str = tabulate(table, headers="firstrow", tablefmt="grid")

                    # Create the embed
                    embed = SmartEmbed(title="📊 API Key Stats", description=f"```\n{table_str}\n```")
                    embeds = embed.create_embeds()

                    # Send the embed
                    for embed in embeds:
                        await interaction.followup.send(embed=embed, ephemeral=True)
                except Exception as e:
                    logger.error(f"An error occurred: {e}")
                    print(f"An error occurred: {e}")  # Fallback print to stdout
            elif action == 'without_key':
                # Defer the response to allow time for processing
                await interaction.response.defer(ephemeral=True)

                try:
                    # Get the guild ID from the interaction
                    guild_id = interaction.guild.id

                    # Fetch all members for the current guild
                    all_members = Member.select().where(Member.guild_id == guild_id)

                    # Create a table using tabulate with multiple members per row
                    rows = []
                    current_row = []
                    max_per_row = 3  # Number of members per row
                    guild = interaction.guild

                    # Iterate over all members and filter those without API keys and with the "Alliance Member" role
                    for member in all_members:
                        discord_member = guild.get_member(member.discord_id)
                        if discord_member and discord.utils.get(discord_member.roles, name="Alliance Member"):
                            api_keys = ApiKey.select().where(ApiKey.member == member)
                            if api_keys.count() == 0:
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
            elif action == 'raw_without_key':
                # Defer the response to allow time for processing
                await interaction.response.defer()

                try:
                    # Get the guild ID from the interaction
                    guild_id = interaction.guild.id

                    # Fetch all members for the current guild
                    all_members = Member.select().where(Member.guild_id == guild_id)

                    # Dictionary to hold roles and corresponding members
                    roles_to_members = defaultdict(list)
                    excluded_roles = {"Alliance Member", "SEA", "NA", "OCX", "Guild Leader", "Guild Officer",
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
                        role_members = "```" + "\n".join(members) + "\n" + "```"
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

            elif action == 'gw2_map_without_key':
                await interaction.response.defer(ephemeral=True)
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
                    await send_large_message(interaction, full_message)
            elif action == 'without_alliance_member':
                await interaction.response.defer(ephemeral=True)

                # Define the roles to check
                roles_to_check = {"DUI", "eA", "SC", "EWW", "PUGS", "PUMP", "bad", "kD", "VIXI", "XXX"}
                excluded_role = "Alliance Member"

                # Check if the "Alliance Member" role exists, and create it if it doesn't
                alliance_member_role = discord.utils.get(interaction.guild.roles, name=excluded_role)

                # List to store matching members
                matching_members = []

                for member in interaction.guild.members:
                    member_roles = {role.name for role in member.roles}
                    if member_roles.intersection(roles_to_check) and excluded_role not in member_roles:
                        role_names = [role.name for role in member.roles if role.name in roles_to_check]
                        matching_members.append(
                            f"{member.name}#{member.discriminator} - Roles: {', '.join(role_names)}")
                        await member.add_roles(alliance_member_role)
                        logger.info(f'Added role "{excluded_role}" to {member.name}#{member.discriminator}')

                # Prepare the message chunks
                chunk_size = 2000
                current_chunk = []
                current_length = 0
                message_chunks = []

                for line in matching_members:
                    line_length = len(line) + 1  # +1 for the newline character
                    if current_length + line_length > chunk_size:
                        message_chunks.append("\n".join(current_chunk))
                        current_chunk = [line]
                        current_length = line_length
                    else:
                        current_chunk.append(line)
                        current_length += line_length

                if current_chunk:
                    message_chunks.append("\n".join(current_chunk))


                # Print the message chunks
                if len(message_chunks) == 0:
                    await interaction.followup.send("No members found", ephemeral=True)
                else:
                    for chunk in message_chunks:
                        await interaction.followup.send(chunk, ephemeral=True)
            elif action == 'create_default_users':
                await interaction.response.defer(ephemeral=True)

                # Define the roles to check
                role = "Alliance Member"
                # List to store matching members
                matching_members = []

                # Check if the "Alliance Member" role exists, and create it if it doesn't
                alliance_member_role = discord.utils.get(interaction.guild.roles, name=role)

                for member in alliance_member_role.members:
                    db_mem = Member.find_or_create(member=member, guild=interaction.guild)
                    if db_mem == 'created':
                        matching_members.append(member.name)

                # Prepare the message chunks
                chunk_size = 2000
                current_chunk = []
                current_length = 0
                message_chunks = []

                for line in matching_members:
                    line_length = len(line) + 1  # +1 for the newline character
                    if current_length + line_length > chunk_size:
                        message_chunks.append("\n".join(current_chunk))
                        current_chunk = [line]
                        current_length = line_length
                    else:
                        current_chunk.append(line)
                        current_length += line_length

                if current_chunk:
                    message_chunks.append("\n".join(current_chunk))

                # Print the message chunks
                if len(message_chunks) == 0:
                    await interaction.followup.send("No members found", ephemeral=True)
                else:
                    for chunk in message_chunks:
                        await interaction.followup.send(chunk, ephemeral=True),
            elif action == 'remove_roles':
                # Defer the response to allow time for processing
                await interaction.response.defer()

                roles_to_check = {"DUI", "eA", "SC", "EWW", "PUGS", "PUMP", "bad", "kD", "VIXI", "XXX",
                                  "Alliance Member"}

                try:
                    # Get the guild and the "Alliance Member" role
                    guild = interaction.guild
                    alliance_member_role = discord.utils.get(guild.roles, name="Alliance Member")

                    # Dictionary to hold roles and corresponding members
                    roles_to_members = defaultdict(list)

                    # Iterate over all members with the "Alliance Member" role
                    for discord_member in guild.members:
                        if alliance_member_role in discord_member.roles:
                            db_member = Member.find_or_create(member=discord_member, guild=guild)

                            if db_member.api_keys.count() == 0:
                                # Collect the roles to remove
                                roles_to_remove = [role for role in discord_member.roles if role.name in roles_to_check]
                                for role in roles_to_remove:
                                    roles_to_members[role.name].append(discord_member.display_name)
                                # Remove the roles
                                await discord_member.remove_roles(*roles_to_remove, reason="Lack of API Key")
                                logger.info(f'Removed roles from {discord_member.name}#{discord_member.discriminator}')
                                # Sleep to avoid hitting rate limits
                                await asyncio.sleep(1)

                    # Prepare the message content
                    message_content = ""
                    for role, members in roles_to_members.items():
                        message_content += f"**{role}**\n" + "\n".join(members) + "\n\n"

                    # Send the message
                    if message_content:
                        await send_large_message(interaction, message_content)
                    else:
                        await interaction.followup.send("No members found without API keys.", ephemeral=True)

                except Exception as e:
                    logger.error(f"An error occurred: {e}")
                    await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)
            elif action == 'ping':
                await interaction.response.defer()

                try:
                    # Get the guild and the "Alliance Member" role
                    guild = interaction.guild
                    guild_id = guild.id
                    alliance_member_role = discord.utils.get(guild.roles, name="Alliance Member")

                    # Dictionary to hold roles and corresponding members
                    roles_to_members = defaultdict(list)
                    excluded_roles = {"Alliance Member", "SEA", "NA", "OCX", "Guild Leader", "Guild Officer",
                                      "Server Booster"}

                    # Iterate over all members with the "Alliance Member" role
                    all_members = Member.select().where(Member.guild_id == guild_id)
                    for member in all_members:
                        discord_member = guild.get_member(member.discord_id)
                        if discord_member and alliance_member_role in discord_member.roles:
                            api_keys = ApiKey.select().where(ApiKey.member == member)
                            if api_keys.count() == 0:
                                # Collect the roles to remove and mention the users
                                for role in discord_member.roles:
                                    if role.name not in excluded_roles and role != guild.default_role:
                                        roles_to_members[role.name].append(discord_member.mention)

                    # Prepare the message chunks
                    message_chunks = []
                    current_chunk = []
                    current_length = 0
                    chunk_size = 2000

                    for role, members in roles_to_members.items():
                        role_header = f"**{role}**\n"
                        role_members = "\n".join(members) + "\n"
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
                        await send_large_message(interaction, chunk)

                except Exception as e:
                    logger.error(f"An error occurred: {e}")
                    await interaction.followup.send(f"An error occurred: {e}")


async def setup(bot):
    for guild in bot.guilds:
        await bot.add_cog(AdminValidateApiCog(bot), guild=guild, override=True)
