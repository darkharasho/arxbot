import discord
import asyncio

from discord.ext import commands
from discord import app_commands
from discord import SelectMenu, SelectOption
from config import settings
from src.gw2_api_client import GW2ApiClient
from peewee import *
from src.models.member import Member
from src.models.config import Config


class VerifyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = SqliteDatabase('arxbot.db')

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
        guild_tags = db_member.gw2_guild_tags()
        gw2_guild_ids = db_member.gw2_guild_ids()
        verify_config = Config.guild_allowed_roles(guild_id=interaction.guild.id)

        roles_to_assign = []
        for tag in guild_tags:
            role = next((r for r in interaction.guild.roles if r.name.lower() == tag.lower()), None)
            if role:
                if role.id in verify_config["allowed_roles"]:
                    roles_to_assign.append(role)

        embed = discord.Embed(title="Verification Results", color=discord.Color.blue())

        if roles_to_assign:
            if verify_config["additional_roles"]:
                for role_id in verify_config["additional_roles"]:
                    role = discord.utils.get(interaction.guild.roles, id=role_id)
                    if role:
                        roles_to_assign.append(role)
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
