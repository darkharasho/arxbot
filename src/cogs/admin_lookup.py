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

    @staticmethod
    def _format_wvw_team_details(team_payload, team_id):
        def extract_team_name(payload):
            if not payload:
                return None

            if isinstance(payload, list):
                if not payload:
                    return None
                payload = payload[0]

            if not isinstance(payload, dict):
                return None

            candidate_keys = (
                "name",
                "team_name",
                "label",
            )
            for key in candidate_keys:
                value = payload.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()

            nested_team = payload.get("team")
            if isinstance(nested_team, dict):
                for key in ("name", "label"):
                    value = nested_team.get(key)
                    if isinstance(value, str) and value.strip():
                        return value.strip()

            return None

        team_name = extract_team_name(team_payload)

        if isinstance(team_payload, list) and team_payload:
            team_payload = team_payload[0]

        region = None
        tier = None
        if isinstance(team_payload, dict):
            region_code = team_payload.get("region")
            if isinstance(region_code, str):
                region_code = region_code.lower()
                region = {
                    "na": "North America",
                    "eu": "Europe",
                }.get(region_code, region_code.upper())
            elif isinstance(region_code, int):
                region = {
                    1: "North America",
                    2: "Europe",
                }.get(region_code)

            tier_value = team_payload.get("tier")
            if isinstance(tier_value, int):
                tier = str(tier_value)

            match_id = team_payload.get("id")
            if isinstance(match_id, str) and "-" in match_id:
                tier_part = match_id.split("-", 1)[1]
                if tier_part.isdigit():
                    tier = tier_part

        if team_name:
            parts = [f"WvW Team: {team_name} ({team_id})"]
            if region:
                parts.append(f"Region: {region}")
            if tier:
                parts.append(f"Tier: {tier}")
            return "; ".join(parts)

        return f"WvW Team ID: {team_id}"

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

                gw2_account_blocks = []
                for api_key in db_member.api_keys:
                    api_client = GW2ApiClient(api_key=api_key.value)
                    try:
                        account_details = api_client.account()
                    except Exception:
                        account_details = None

                    account_lines = [f"- {api_key.name}"]
                    detail_parts = []

                    if account_details:
                        wvw_rank = account_details.get("wvw_rank")
                        if wvw_rank is not None:
                            detail_parts.append(f"WvW Rank: {wvw_rank}")

                        commander_tag = account_details.get("commander")
                        if commander_tag is not None:
                            detail_parts.append(f"Commander: {'Yes' if commander_tag else 'No'}")

                        team_id = account_details.get("wvw_team")
                        if team_id:
                            try:
                                team_details = api_client.wvw_team_by_id(team_id)
                            except Exception:
                                team_details = None

                            detail_parts.append(self._format_wvw_team_details(team_details, team_id))

                    if detail_parts:
                        account_lines.extend([f"    {part}" for part in detail_parts])
                    elif account_details is None:
                        account_lines.append("    Unable to fetch account details")

                    gw2_account_blocks.append("\n".join(account_lines))

                embed.add_field(name="GW2 Accounts", value="```" + "\n\n".join(gw2_account_blocks) + "```",
                                inline=False)
            else:
                embed.add_field(name="API Keys", value="```No API Keys found```", inline=False)
            await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    for guild in bot.guilds:
        await bot.add_cog(AdminLookup(bot), guild=guild, override=True)
