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

        # Build db_members for quick lookup
        db_members = {m.gw2_username: m for m in Member.select() if m.gw2_username}

        # 1. Members where wvw_member is False
        non_wvw_members = {m['name'] for m in gw2_members if not m.get('wvw_member', False) and m.get('name')}
        # 2. Members with no corresponding Member.api_key
        no_api_key_members = {
            m['name']
            for m in gw2_members
            if m.get('name') and (m['name'] not in db_members or not db_members[m['name']].api_key)
        }
        # 3. Discord "Alliance Member" role holders not in GW2 guild
        alliance_role = discord.utils.get(interaction.guild.roles, name="Alliance Member")
        discord_alliance_members = [m for m in interaction.guild.members if alliance_role in m.roles]
        discord_gw2_names = set()
        for member in discord_alliance_members:
            db_member = Member.select().where(Member.username == member.name).first()
            if db_member and db_member.gw2_username:
                discord_gw2_names.add(db_member.gw2_username)
        not_in_gw2_guild = {name for name in discord_gw2_names if name not in gw2_names_lower}

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

        # Helper to get guilds for a member
        def get_guilds_for_member(member_obj):
            if member_obj and member_obj.api_key:
                try:
                    return ", ".join(member_obj.api_key.member.gw2_guild_names())
                except Exception:
                    return ""
            return ""

        # Helper to get Discord username for a GW2 username
        def get_discord_name(gw2_name):
            member_obj = db_members.get(gw2_name, None)
            return member_obj.username if member_obj else ""

        # Prepare CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["GW2 Username", "Discord Username", "Infraction", "Guild"])

        for name, infraction_list in infractions.items():
            member_obj = db_members.get(name, None)
            discord_name = member_obj.username if member_obj else ""
            guilds = get_guilds_for_member(member_obj)
            writer.writerow([name, discord_name, ", ".join(infraction_list), guilds])

        output.seek(0)
        csv_file = discord.File(fp=io.BytesIO(output.getvalue().encode()), filename="relink_report.csv")
        await interaction.followup.send("Here is the relink report:", file=csv_file, ephemeral=True)

async def setup(bot):
    for guild in bot.guilds:
        await bot.add_cog(AdminRelinkCog(bot), guild=guild, override=True)
