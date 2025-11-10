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

                            team_name = None
                            if isinstance(team_details, dict):
                                team_name = team_details.get("name")
                            elif isinstance(team_details, list) and team_details:
                                team_name = team_details[0].get("name")

                            if team_name:
                                detail_parts.append(f"WvW Team: {team_name} ({team_id})")
                            else:
                                detail_parts.append(f"WvW Team ID: {team_id}")

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
