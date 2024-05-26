import discord
import asyncio

from discord.ext import commands
from discord import app_commands
from discord import SelectMenu, SelectOption
from config import settings
from src.gw2_api_client import GW2ApiClient
from src.tasks.stat_updater_task import StatUpdaterTask
from peewee import *
from src.models.member import Member
from src.models.api_key import ApiKey

class RemoveKeyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = SqliteDatabase('arxbot.db')

    @app_commands.command(
        name="remove-key",
        description="Remove an API key"
    )
    async def remove_key(self, interaction):
        await interaction.response.defer(ephemeral=True)
        db_member = Member.find_or_create(interaction.user)
        embed = discord.Embed(
            title="Remove Key",
            description=""
        )
        options = []
        for api_key in db_member.api_keys:
            options.append(
                discord.SelectOption(label=api_key.name, value=api_key.id)
            )
            if api_key.primary:
                key_name = f"{api_key.name} - Primary"
            else:
                key_name = api_key.name
            embed.add_field(name=f"{key_name} {'✦' if api_key.primary else ''}", value=f"```{api_key.value}```", inline=False)
        key_select_menu = discord.ui.Select(
            placeholder="Select API Key...",
            options=options
        )
        view = discord.ui.View()
        view.add_item(key_select_menu)

        response = await interaction.followup.send(embed=embed, view=view)

        events = [
            self.bot.wait_for('interaction')
        ]

        # with asyncio.FIRST_COMPLETED, this triggers as soon as one of the events is fired
        done, pending = await asyncio.wait(events, return_when=asyncio.FIRST_COMPLETED)
        event = done.pop().result()

        # cancel the other check
        for future in pending:
            future.cancel()

        if type(event) == discord.Interaction:
            await event.response.defer()
            embed = discord.Embed(title="Remove API Key", description="")
            member = Member.select().where(Member.discord_id == interaction.user.id).first()
            api_key = ApiKey.select().where(ApiKey.id == event.data['values'][0]).first()
            was_primary = api_key.primary
            if api_key.member == member:
                api_key.delete_instance()
                if len(member.api_keys) >= 1 and was_primary:
                    new_primary_key = member.api_keys.first()
                    new_primary_key.primary = True
                    new_primary_key.save()
                    embed.description = f"Removed key. New primary is {new_primary_key.name}"
                else:
                    embed.description = "Removed key."
            else:
                embed.description = "Hmm. This doesn't appear to be your key."
            await response.edit(embed=embed, view=None)


async def setup(bot):
    for guild in bot.guilds:
        await bot.add_cog(RemoveKeyCog(bot), guild=guild, override=True)
