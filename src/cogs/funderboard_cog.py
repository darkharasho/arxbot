import pdb

import discord
import asyncio  # Import asyncio to use asyncio.gather

from discord.ext import commands
from discord import app_commands
from config import settings
from tabulate import tabulate
from src.models.member import Member
from src.models.api_key import ApiKey
from peewee import SqliteDatabase  # Import SqliteDatabase

tabulate.PRESERVE_WHITESPACE = True


async def calculate_leaderboard(name, data, guild_id, guild):
    # Optimize query to fetch only required fields and related members
    query = (
        ApiKey.select(ApiKey.member, Member.username, Member.discord_id, Member.gw2_stats, Member.gw2_username)
        .join(Member)
        .where((ApiKey.guild_id == guild_id) & (ApiKey.leaderboard_enabled == True))
    )

    leaderboard = {}
    alliance_role = discord.utils.get(guild.roles, name="Alliance Member")  # Get the "Alliance Member" role

    # Create a dictionary of cached members for quick lookup
    cached_members = {member.id: member for member in guild.members}

    for api_key in query:
        member = api_key.member

        # Skip if discord_id is missing
        if not member.discord_id:
            continue

        # Use the cached member instead of fetching from the API
        discord_member = cached_members.get(member.discord_id)
        if not discord_member:
            continue

        # Skip if the Discord member does not have the "Alliance Member" role
        if alliance_role not in discord_member.roles:
            continue

        # Ensure the member has the required attribute or method
        if not hasattr(member, data):
            continue

        try:
            # Fetch the required data dynamically
            value = getattr(member, data)()

            # Add to leaderboard only if the username is not already present
            if member.username not in leaderboard:
                leaderboard[member.username] = [member.username, member.gw2_username, value]
        except Exception:
            continue  # Gracefully skip this iteration

    # Convert the leaderboard dictionary to a list and sort it
    sorted_leaderboard = sorted(
        leaderboard.values(),
        key=lambda x: (x[2] != "∞", x[2]),  # Sort by whether the value is "∞" first, then by the value itself
        reverse=True
    )[:settings.MAX_LEADERBOARD_MEMBERS]

    # Ensure `.harasho` is always first
    harasho_entry = leaderboard.get(".harasho", [".harasho", "Unknown GW2 Username", "∞"])
    sorted_leaderboard.insert(0, harasho_entry)  # Insert `.harasho` at the beginning

    # Remove duplicates if `.harasho` was already in the sorted list
    sorted_leaderboard = [entry for i, entry in enumerate(sorted_leaderboard) if entry not in sorted_leaderboard[:i]]

    # Limit the leaderboard to the maximum number of members
    sorted_leaderboard = sorted_leaderboard[:settings.MAX_LEADERBOARD_MEMBERS]

    index = range(1, len(sorted_leaderboard) + 1)

    # Generate the table
    headers = ["Name", "GW2 Username", f"{name}"]
    table = tabulate(
        sorted_leaderboard,
        headers,
        tablefmt="simple",
        showindex=index,
        maxcolwidths=[23, 23, None]
    )

    return table


class FunderboardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = SqliteDatabase('arxbot.db')  # Initialize the database

    @app_commands.command(
        name="funderboard",
        description="Fun Leaderboard Stats"
    )
    async def funderboard(self, interaction):
        await interaction.response.defer()

        # Run leaderboard calculations in parallel
        spike_table, supply_table, yak_table = await asyncio.gather(
            calculate_leaderboard("Spikes", "legendary_spikes", guild_id=interaction.guild.id, guild=interaction.guild),
            calculate_leaderboard("Supply", "weekly_supply_spent", guild_id=interaction.guild.id, guild=interaction.guild),
            calculate_leaderboard("Yaks", "weekly_yaks_escorted", guild_id=interaction.guild.id, guild=interaction.guild),
        )

        # Create and send the embed
        embed = discord.Embed(
            title="🎉 Funderboard",
            description=f"〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️"
                        f"**🏆 Legendary Spikes:**```{spike_table}```\n"
                        f"**📦 Weekly Repair Masters:**```{supply_table}```\n"
                        f"**🐄 Weekly Yak Escorts:**```{yak_table}```\n"
        )

        await interaction.followup.send(embed=embed)


async def setup(bot):
    for guild in bot.guilds:
        await bot.add_cog(FunderboardCog(bot), guild=guild, override=True)
