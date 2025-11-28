import re
import csv
import io
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from config import settings
from src.gw2_api_client import GW2ApiClient
from src.models.api_key import ApiKey
from src.models.member import Member


class AdminManualRelinkCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="admin_manual_relink",
        description="Admin: Generate a relink CSV based on a provided list of GW2 usernames",
    )
    @app_commands.describe(
        usernames="Comma or newline separated list of GW2 account names (e.g. Example.1234, Another.5678)",
    )
    async def admin_manual_relink(self, interaction: discord.Interaction, usernames: str):
        await interaction.response.defer(ephemeral=True)

        parsed_names = [
            name.strip()
            for name in re.split(r"[\n,]", usernames)
            if name and name.strip()
        ]

        if not parsed_names:
            await interaction.followup.send(
                "Please provide at least one GW2 username.", ephemeral=True
            )
            return

        # Normalize names while preserving order
        seen = set()
        ordered_names = []
        for name in parsed_names:
            if name not in seen:
                ordered_names.append(name)
                seen.add(name)

        gw2_client = GW2ApiClient()
        guild_id = settings.GW2_GUILD_ID
        gw2_members = gw2_client.get_guild_members(guild_id)
        gw2_members_by_name = {
            m.get("name", "").strip(): m
            for m in gw2_members
            if m.get("name") and m.get("name").strip()
        }
        db_members = {
            m.gw2_username.strip(): m
            for m in Member.select()
            if m.gw2_username and m.gw2_username.strip()
        }

        api_key_members = {
            ak.name.strip(): ak.member
            for ak in ApiKey.select().where(ApiKey.guild_id == interaction.guild.id)
            if ak.name and ak.name.strip() and ak.member
        }

        api_key_names = set(api_key_members.keys())

        def get_roles_for_member(member_obj: Member):
            if not member_obj:
                return ""
            discord_member = interaction.guild.get_member(member_obj.discord_id)
            if not discord_member:
                return ""
            excluded_roles = {"@everyone", "Alliance Member", "Guild Leader", "Guild Officer", "Announcer"}
            return ", ".join(
                role.name for role in discord_member.roles if role.name not in excluded_roles
            )

        output = io.StringIO()
        writer = csv.writer(output)

        for name in ordered_names:
            member_obj = db_members.get(name) or api_key_members.get(name)

            infractions = []
            guild_member = gw2_members_by_name.get(name)
            if guild_member:
                if not guild_member.get("wvw_member", False):
                    infractions.append("Not WvW Member")
            else:
                infractions.append("Not in GW2 Guild")

            if name not in api_key_names:
                infractions.append("No API Key")

            discord_name = member_obj.username if member_obj else ""
            roles = get_roles_for_member(member_obj)
            writer.writerow([name, discord_name, ", ".join(infractions), "", "", roles, ""])

        output.seek(0)
        date_str = datetime.now().strftime("%Y-%m-%d")
        file_name = f"manual_relink_report_{date_str}.csv"
        csv_file = discord.File(fp=io.BytesIO(output.getvalue().encode()), filename=file_name)
        await interaction.followup.send(
            "Here is the relink report for the provided names:",
            file=csv_file,
            ephemeral=True,
        )


async def setup(bot):
    for guild in bot.guilds:
        await bot.add_cog(AdminManualRelinkCog(bot), guild=guild, override=True)
