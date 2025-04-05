import sys
import discord
import discord.ui
from discord.ext import commands
from discord import app_commands
from peewee import *
from lib.api_key_processor import ApiKeyProcessor  # Import the new ApiKeyProcessor class
from src.models.member import Member
from src.models.api_key import ApiKey
from src.tasks.stat_updater_task import StatUpdaterTask


class AddKeyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = SqliteDatabase('eww_bot.db')

    async def process_key(self, interaction, gw2_api_key: str, primary: bool = True):
        # Use the new ApiKeyProcessor to handle the API key processing
        result = await ApiKeyProcessor.process_key(interaction, gw2_api_key=gw2_api_key)
        api_checks = result["api_checks"]
        successful_permissions = result["successful_permissions"]
        db_member = result["db_member"]
        api_client = result["api_client"]
        response = result["response"]
        embed = result["embed"]

        # Save successful permissions in the database
        if api_checks["account"]:
            other_keys = db_member.api_keys
            name = api_client.account()["name"]
            embed.title = "Validating API Key..."
            embed.clear_fields()
            embed.add_field(name="🔃 Checking Guild Wars 2 accounts...", value="")
            embed.add_field(name="🔃 Checking primary key status...", value="")
            await response.edit(embed=embed)

            for other_key in other_keys:
                if api_client.account()["id"] == other_key.account_id():
                    embed = discord.Embed(
                        title="Guild Wars 2 API Key - Account already Registered",
                        description="If you'd like to change your API key, remove the other one first with `/remove-key`",
                        color=0xff0000
                    )
                    embed.add_field(
                        name="Proposed GW2 API Key",
                        value=f"```\n{name}\n\n{gw2_api_key}```",
                        inline=False
                    )
                    embed.add_field(
                        name="Current GW2 API Key",
                        value=f"```\n{other_key.name}\n\n{other_key.value}```",
                        inline=False
                    )
                    await response.edit(embed=embed)
                    return

            embed.set_field_at(index=0, name="✅ Guild Wars 2 accounts verified", value="")
            await response.edit(embed=embed)

            if primary is False and len(other_keys) == 0:
                embed = discord.Embed(
                    title="Guild Wars 2 API Key - You must have a primary key",
                    color=0xff0000
                )
                embed.add_field(name="GW2 API Key", value=f"```{gw2_api_key}```", inline=False)
                embed.add_field(name="Primary?", value=primary)
                await response.edit(embed=embed)
                return

            embed.set_field_at(index=1, name="✅ Primary key verified", value="")
            await response.edit(embed=embed)

            try:
                full_key = all(api_checks.values())
                api_key = ApiKey.create(
                    member=db_member,
                    name=name,
                    value=gw2_api_key,
                    primary=primary,
                    leaderboard_enabled=full_key,
                    guild_id=interaction.guild.id,
                    permissions=",".join(successful_permissions)  # Save permissions as a comma-separated string
                )
                if primary and other_keys:
                    for other_key in other_keys:
                        if other_key != api_key:
                            other_key.primary = False
                            other_key.save()

                embed = discord.Embed(
                    title="Guild Wars 2 API Key",
                    description=f"**API key registered for:** {interaction.user.mention}",
                    color=0x0ff000
                )
                embed.add_field(name="Name", value=f"```{name}```")
                embed.add_field(name="Primary?", value=f"```{primary}```")
                embed.add_field(name="Key", value=f"```{gw2_api_key}```", inline=False)
                embed.add_field(name="Permissions", value=", ".join(successful_permissions), inline=False)
                await response.edit(embed=embed)
            except IntegrityError:
                embed = discord.Embed(
                    title="Guild Wars 2 API Key - Key already registered",
                    color=0xff0000
                )
                embed.add_field(name="GW2 API Key", value=f"```{gw2_api_key}```", inline=False)
                await response.edit(embed=embed)
        else:
            embed = discord.Embed(
                title="Guild Wars 2 API Key - Invalid GW2 API Key or Insufficient Permissions",
                color=0xff0000
            )
            for api_check in result["api_checks_display"]:
                embed.add_field(name=api_check, value="")
            embed.add_field(name="", value="")
            embed.add_field(name="GW2 API Key", value=f"```{gw2_api_key}```", inline=False)
            await response.edit(embed=embed)

    @app_commands.command(
        name="add-key",
        description="Add an API Key. Requires: account, Optional: characters, progression, inventories, and builds"
    )
    async def add_key(self, interaction, gw2_api_key: str, primary: bool = True):
        await self.process_key(interaction=interaction, gw2_api_key=gw2_api_key, primary=primary)

    @app_commands.command(
        name="api-key",
        description="(Alias for /add-key) Requires: account, Optional: characters, progression, inventories, and builds"
    )
    async def api_key(self, interaction, gw2_api_key: str, primary: bool = True):
        await self.process_key(interaction=interaction, gw2_api_key=gw2_api_key, primary=primary)

    @app_commands.command(
        name="alt-api-key",
        description="Add an API key for an alt account. Requires: account, Optional: characters, progression"
    )
    async def alt_api_key(self, interaction, gw2_api_key: str):
        await self.process_key(interaction=interaction, gw2_api_key=gw2_api_key, primary=False)


async def setup(bot):
    for guild in bot.guilds:
        await bot.add_cog(AddKeyCog(bot), guild=guild, override=True)
