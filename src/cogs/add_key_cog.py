import sys
import pdb
import discord
import discord.ui
from discord.ext import commands
from discord import app_commands
from config import settings
from src.gw2_api_client import GW2ApiClient
from src.tasks.stat_updater_task import StatUpdaterTask
from src.models.member import Member
from src.models.api_key import ApiKey
from peewee import *


class AddKeyCog(commands.Cog):
    def __init__(self, bot):
        # pdb.set_trace()
        self.bot = bot
        self.db = SqliteDatabase('eww_bot.db')

    async def process_key(self, interaction, gw2_api_key: str, primary: bool = True):
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(
            title="Checking API key...",
            description=f"```{gw2_api_key}```"
        )
        embed.add_field(name="Permissions", value="", inline=False)
        for check in ["🔃 Account", "🔃 Progression", "🔃 Characters", "🔃 Builds", "🔃 Inventories"]:
            embed.add_field(name=check, value="")
        embed.add_field(name="", value="")

        response = await interaction.followup.send(embed=embed, ephemeral=True)
        db_member = Member.find_or_create(member=interaction.user, guild=interaction.guild)
        api_client = GW2ApiClient(api_key=gw2_api_key)
        api_checks = {}
        api_checks_display = []
        try:
            if not api_client.account():
                raise
            api_checks["account"] = True
            api_checks_display.append("✅ Account")
            embed.set_field_at(index=1, name="✅ Account", value="", inline=True)
            await response.edit(embed=embed)
        except:
            api_checks["account"] = False
            api_checks_display.append("❌ Account")
            embed.set_field_at(index=1, name="❌ Account", value="", inline=True)
            await response.edit(embed=embed)

        try:
            if not api_client.account_achievements():
                raise
            api_checks["account_achievements"] = True
            api_checks_display.append("✅ Progression")
            embed.set_field_at(index=2, name="✅ Progression", value="", inline=True)
            await response.edit(embed=embed)
        except:
            api_checks["account_achievements"] = False
            api_checks_display.append("⚠️ Progression")
            embed.set_field_at(index=2, name="⚠️ Progression", value="", inline=True)
            await response.edit(embed=embed)

        try:
            if not api_client.characters():
                raise
            api_checks["characters"] = True
            api_checks_display.append("✅ Characters")
            embed.set_field_at(index=3, name="✅ Characters", value="", inline=True)
            await response.edit(embed=embed)
        except:
            api_checks["characters"] = False
            api_checks_display.append("⚠️ Characters")
            embed.set_field_at(index=3, name="⚠️ Characters", value="", inline=True)
            await response.edit(embed=embed)

        try:
            if not api_client.builds(index=0, tabs="all"):
                raise
            api_checks["builds"] = True
            api_checks_display.append("✅ Builds")
            embed.set_field_at(index=4, name="✅ Builds", value="", inline=True)
            await response.edit(embed=embed)
        except:
            api_checks["builds"] = False
            api_checks_display.append("⚠️ Builds")
            embed.set_field_at(index=4, name="⚠️ Builds", value="", inline=True)
            await response.edit(embed=embed)
        try:
            if not api_client.bank():
                raise
            api_checks["bank"] = True
            api_checks_display.append("✅ Inventories")
            embed.set_field_at(index=5, name="✅ Inventories", value="", inline=True)
            await response.edit(embed=embed)
        except:
            api_checks["bank"] = False
            api_checks_display.append("⚠️ Inventories")
            embed.set_field_at(index=5, name="⚠️ Inventories", value="", inline=True)
            await response.edit(embed=embed)

        if api_checks["account"]:
            other_keys = db_member.api_keys
            account_data = GW2ApiClient(api_key=gw2_api_key).account()
            if not account_data or "name" not in account_data:
                embed = discord.Embed(
                    title="Guild Wars 2 API Key - Invalid GW2 API Key or Insufficient Permissions",
                    color=0xff0000)
                embed.add_field(name="GW2 API Key", value=f"```{gw2_api_key}```", inline=False)
                await response.edit(embed=embed)
                return
            name = account_data["name"]
            embed.title = "Validating API Key..."
            embed.clear_fields()
            embed.add_field(name="🔃 Checking Guild Wars 2 accounts...", value="")
            embed.add_field(name="🔃 Checking primary key status...", value="")
            await response.edit(embed=embed)
            for other_key in other_keys:
                if api_client.account()["id"] == other_key.account_id():
                    embed = discord.Embed(
                        title="Guild Wars 2 API Key - Account already Registered",
                        description="If you'd like to change your API key, remove the other one first wtih `/remove-key`",
                        color=0xff0000)
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
                    color=0xff0000)
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
                    guild_id=interaction.guild.id
                )
                # --- NEW: Fetch and store guild names ---
                try:
                    account_data = api_client.account()
                    guild_ids = account_data.get("guilds", [])
                    guild_names = []
                    for guild_id in guild_ids:
                        try:
                            guild_info = api_client.guild(gw2_guild_id=guild_id)
                            if isinstance(guild_info, dict):
                                gname = guild_info.get("name")
                                if gname:
                                    guild_names.append(gname)
                        except Exception as e:
                            print(f"Failed to fetch guild info for {guild_id}: {e}")
                    api_key.guild_names = guild_names
                    api_key.save()
                except Exception as e:
                    print(f"Failed to fetch or save guild names: {e}")
                # --- END NEW ---

                if primary and other_keys:
                    for other_key in other_keys:
                        if other_key == api_key:
                            pass
                        else:
                            other_key.primary = False
                            other_key.save()
                if full_key:
                    embed.title = "Syncing Guild Wars 2 Data..."
                    embed.clear_fields()
                    for item in ["🔃 Syncing Kill Count...", "🔃 Syncing Capture Count...", "🔃 Syncing Rank Count...", "🔃 Syncing Death Count...", "🔃 Syncing Repair Count...", "🔃 Syncing Yak Count..."]:
                        embed.add_field(name=item, value="", inline=False)
                    await response.edit(embed=embed)
                    suc = StatUpdaterTask(self.bot)
                    await suc.update_kill_count(db_member)
                    embed.set_field_at(index=0, name="✅ Kill Count Synced", value="", inline=False)
                    await response.edit(embed=embed)
                    await suc.update_capture_count(db_member)
                    embed.set_field_at(index=1, name="✅ Capture Count Synced", value="", inline=False)
                    await response.edit(embed=embed)
                    await suc.update_rank_count(db_member)
                    embed.set_field_at(index=2, name="✅ Rank Count Synced", value="", inline=False)
                    await response.edit(embed=embed)
                    await suc.update_deaths_count(db_member)
                    embed.set_field_at(index=3, name="✅ Death Count Synced", value="", inline=False)
                    await response.edit(embed=embed)
                    await suc.update_supply_spent(db_member)
                    embed.set_field_at(index=4, name="✅ Supply Count Synced", value="", inline=False)
                    await response.edit(embed=embed)
                    await suc.update_yaks_escorted(db_member)
                    embed.set_field_at(index=5, name="✅ Yak Count Synced", value="", inline=False)
                    await response.edit(embed=embed)

                embed = discord.Embed(
                    title="Guild Wars 2 API Key",
                    description=f"**API key registered for:** {interaction.user.mention}",
                    color=0x0ff000)
                embed.add_field(name="Name", value=f"```{name}```")
                embed.add_field(name="Primary?", value=f"```{primary}```")
                embed.add_field(name="Key", value=f"```{gw2_api_key}```", inline=False)
                embed.add_field(name="Permissions", value="", inline=False)
                for api_check in api_checks_display:
                    embed.add_field(name=api_check, value="")
                embed.add_field(name="", value="")
                response = await response.edit(embed=embed)

                await response.edit(embed=embed)
            except IntegrityError:
                embed = discord.Embed(
                    title="Guild Wars 2 API Key - Key already registered",
                    color=0xff0000)
                embed.add_field(name="GW2 API Key", value=f"```{gw2_api_key}```", inline=False)
                await response.edit(embed=embed)
        else:
            embed = discord.Embed(
                title="Guild Wars 2 API Key - Invalid GW2 API Key or Insufficient Permissions",
                color=0xff0000)
            for api_check in api_checks_display:
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
        description="Add an API key for an alt acount. Requires: account, Optional: characters, progression"
    )
    async def alt_api_key(self, interaction, gw2_api_key: str):
        await self.process_key(interaction=interaction, gw2_api_key=gw2_api_key, primary=False)


async def setup(bot):
    for guild in bot.guilds:
        await bot.add_cog(AddKeyCog(bot), guild=guild, override=True)
