import pdb
import discord
import json
import textwrap
import asyncio
import csv
import io

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

class AdminRelinkCog(commands.Cog):
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
        name="admin_relink_cog",
        description="Admin: Get a prepared list of members who do not meet the criteria for the relink"
    )
    async def admin_relink_cog(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        gw2_client = GW2ApiClient()
        guild_id = settings.GW2_GUILD_ID

        # 1. Get all GW2 guild members
        gw2_members = gw2_client.get_guild_members(guild_id)
        gw2_names = {m['name'] for m in gw2_members}
        gw2_names_lower = {n for n in gw2_names}

        # Build db_members for quick lookup (normalize and strip whitespace)
        db_members = {
            m.gw2_username.strip(): m
            for m in Member.select()
            if m.gw2_username and m.gw2_username.strip()
        }

        # Build ApiKey lookup to find Discord members by GW2 account name
        api_key_members = {
            ak.name.strip(): ak.member
            for ak in ApiKey.select().where(ApiKey.guild_id == interaction.guild.id)
            if ak.name and ak.name.strip()
        }

        # 1. Members where wvw_member is False
        non_wvw_members = {m['name'].strip() for m in gw2_members if m.get('name') and not m.get('wvw_member', False)}

        # 2. Members with no corresponding ApiKey for this guild and GW2 name
        no_api_key_members = set()
        for m in gw2_members:
            gw2_name = m.get('name')
            if not gw2_name:
                continue
            gw2_name_stripped = gw2_name.strip()
            keys = ApiKey.select().where(
                (ApiKey.guild_id == interaction.guild.id) &
                (ApiKey.name == gw2_name_stripped)
            )
            if keys.count() == 0:
                no_api_key_members.add(gw2_name_stripped)

        # 3. Discord "Alliance Member" role holders not in GW2 guild
        alliance_role = discord.utils.get(interaction.guild.roles, name="Alliance Member")
        discord_alliance_members = [m for m in interaction.guild.members if alliance_role in m.roles]
        discord_gw2_names = set()
        not_in_gw2_guild = set()
        gw2_names_set = {n.strip() for n in gw2_names}

        for member in discord_alliance_members:
            db_member = Member.select().where(Member.username == member.name).first()
            if db_member and db_member.gw2_username:
                # Check all API keys for this member
                api_keys = list(db_member.api_keys)
                # If any API key's name is in the GW2 guild, skip
                in_guild = False
                for api_key in api_keys:
                    if api_key.name and api_key.name.strip() in gw2_names_set:
                        in_guild = True
                        break
                if not in_guild:
                    discord_gw2_names.add(db_member.gw2_username.strip())
                    not_in_gw2_guild.add(db_member.gw2_username.strip())

        # Aggregate infractions
        all_names = non_wvw_members | no_api_key_members | not_in_gw2_guild
        infractions = {}
        for name in all_names:
            infractions[name] = []
            if name in non_wvw_members:
                infractions[name].append("Not WvW Member")
            if name in no_api_key_members:
                infractions[name].append("No API Key")
            if name in not_in_gw2_guild:
                infractions[name].append("Alliance Member not in GW2 Guild")

        # Helper to get Discord roles for a member
        def get_roles_for_member(member_obj):
            if not member_obj:
                return ""
            discord_member = interaction.guild.get_member(member_obj.discord_id)
            if not discord_member:
                return ""
            # Exclude specified roles
            excluded_roles = {"@everyone", "Alliance Member", "Guild Leader", "Guild Officer", "Announcer"}
            return ", ".join(
                role.name for role in discord_member.roles
                if role.name not in excluded_roles
            )

        # Prepare CSV
        output = io.StringIO()
        writer = csv.writer(output)
        # No header row

        for name, infraction_list in infractions.items():
            member_obj = db_members.get(name, None)

            if not member_obj:
                member_obj = api_key_members.get(name, None)

            discord_name = member_obj.username if member_obj else ""
            guild_name = ""
            if member_obj and getattr(member_obj, "guild_id", None):
                guild_name = getattr(member_obj.guild_id, "name", "")

            roles = get_roles_for_member(member_obj)
            infraction = ", ".join(infraction_list)
            # Kicked?, Immune, Notes left blank for manual use in Google Sheets
            writer.writerow([name, discord_name, guild_name, infraction, "", "", roles, ""])

        output.seek(0)
        date_str = datetime.now().strftime("%Y-%m-%d")
        file_name = f"relink_report_{date_str}.csv"
        csv_file = discord.File(fp=io.BytesIO(output.getvalue().encode()), filename=file_name)
        await interaction.followup.send("Here is the relink report:", file=csv_file, ephemeral=True)

async def setup(bot):
    for guild in bot.guilds:
        await bot.add_cog(AdminRelinkCog(bot), guild=guild, override=True)
