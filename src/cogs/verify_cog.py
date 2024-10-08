import pdb

import discord
import asyncio

from discord.ext import commands, tasks
from discord import app_commands
from discord import SelectMenu, SelectOption
from config import settings
from src.gw2_api_client import GW2ApiClient
from peewee import *
from src.models.member import Member
from src.models.config import Config
from src.lib.logger import logger


class VerifyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = SqliteDatabase('arxbot.db')
        # self.verify_members.start()  # Start the scheduled task

    # def cog_unload(self):
    #     self.verify_members.cancel()  # Stop the task when the cog is unloaded

    # @tasks.loop(hours=24)
    # async def verify_members(self):
    #     return
    #     for guild in self.bot.guilds:
    #         verify_config = Config.guild_allowed_roles(guild_id=guild.id)
    #         async for member in guild.fetch_members(limit=None):
    #             db_member = Member.find_or_create(member=member, guild=guild)
    #             if len(db_member.api_keys) == 0:
    #                 continue  # Skip members without API keys
    #
    #             gw2_guild_ids = db_member.gw2_guild_ids()
    #             roles_to_assign = []
    #             roles_to_remove = []
    #             for guild_mapping in verify_config["gw2_to_discord_mapping"]:
    #                 role = discord.utils.get(guild.roles, id=int(guild_mapping['discord_role_id']))
    #                 if guild_mapping["guild_id"] in gw2_guild_ids and role not in member.roles:
    #                     roles_to_assign.append(role)
    #                 if guild_mapping["guild_id"] not in gw2_guild_ids and role in member.roles:
    #                     roles_to_remove.append(role)
    #
    #             try:
    #                 if roles_to_assign:
    #                     await member.add_roles(*roles_to_assign)
    #                     logger.info(f"[Add Roles] - {member.name} - {', '.join(r.name for r in roles_to_assign)}")
    #                 if roles_to_remove:
    #                     await member.remove_roles(*roles_to_remove)
    #                     logger.info(f"[Remove Roles] - {member.name} - {', '.join([r.name for r in roles_to_remove])}")
    #             except discord.Forbidden:
    #                 logger.warning(f"Failed to update roles for {member.display_name} due to missing permissions.")
    #             except discord.HTTPException as e:
    #                 logger.warning(f"Failed to update roles for {member.display_name} due to an error: {e}")

    # @verify_members.before_loop
    # async def before_verify_members(self):
    #     await self.bot.wait_until_ready()

    @app_commands.command(
        name="verify",
        description="Verify guild membership"
    )
    async def verify(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        db_member = Member.find_or_create(interaction.user, guild=interaction.guild)
        if len(db_member.api_keys) == 0:
            embed = discord.Embed(
                title="Verification Results",
                color=discord.Color.red(),
                description=f"You have no API keys! Use `/api-key` to add one."
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        gw2_guild_ids = db_member.gw2_guild_ids()
        if len(gw2_guild_ids) == 0:
            embed = discord.Embed(
                title="Verification Results",
                color=discord.Color.red(),
                description=f"You have no guilds. This can happen because of a bad api key / for whatever reason GW2 API needs the Guilds."
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        verify_config = Config.guild_allowed_roles(guild_id=interaction.guild.id)

        roles_to_assign = []
        for guild_mapping in verify_config["gw2_to_discord_mapping"]:
            role = discord.utils.get(interaction.guild.roles, id=int(guild_mapping['discord_role_id']))
            if guild_mapping["guild_id"] in gw2_guild_ids:
                roles_to_assign.append(role)

        embed = discord.Embed(title="Verification Results", color=discord.Color.blue())

        if roles_to_assign:
            try:
                await interaction.user.add_roles(*roles_to_assign)
                role_mentions = [role.mention for role in roles_to_assign]
                embed.add_field(name="Roles Assigned", value='\n'.join(role_mentions), inline=False)
                embed.set_footer(text="Verification successful!")
            except discord.Forbidden:
                embed.description = "I don't have permission to assign one or more of the roles."
                embed.color = discord.Color.red()
            except discord.HTTPException as e:
                embed.description = f"Failed to assign roles due to an error: {e}"
                embed.color = discord.Color.red()
        else:
            embed.description = "No matching roles found."
            embed.color = discord.Color.orange()

        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    for guild in bot.guilds:
        await bot.add_cog(VerifyCog(bot), guild=guild, override=True)
