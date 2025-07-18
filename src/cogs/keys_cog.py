import discord
import discord.ui
from discord.ext import commands
from discord import app_commands
from config import settings
from src.gw2_api_client import GW2ApiClient
from src.tasks.stat_updater_task import StatUpdaterTask
from peewee import *
from src.models.member import Member

class KeysCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = SqliteDatabase('eww_bot.db')

    @app_commands.command(
        name="keys",
        description="Check your GW2 API Keys"
    )
    async def keys(self, interaction):
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(
            title="Guild Wars 2 API Keys",
            description=f"",
            color=0x0ff000)
        member = Member.select().where(Member.discord_id == interaction.user.id).first()
        for api_key in member.api_keys:
            world_info = api_key.api_client().world()
            account_info = api_key.api_client().account()
            server = world_info["name"] if world_info and "name" in world_info else "Unknown"
            rank = account_info.get("wvw", {}).get("rank", "Unknown") if account_info else "Unknown"
            value = f"""
            **Server**: {server}
            **Rank**: {rank}
            **Key**: 
            ```{api_key.value}```
            """
            embed.add_field(name=f"{api_key.name} {'✦' if api_key.primary else ''}", value=value, inline=False)

        await interaction.followup.send(embed=embed)


async def setup(bot):
    for guild in bot.guilds:
        await bot.add_cog(KeysCog(bot), guild=guild, override=True)
