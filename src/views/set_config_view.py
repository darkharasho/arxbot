import pdb

import discord
import tabulate
import asyncio
from discord.ext import commands
from config import settings
from src import helpers
from src import authorization
from discord.ui import Button, View, Select
from discord import SelectMenu, SelectOption
from tabulate import SEPARATING_LINE
from src.views import set_multi_config_view
from src.models.config import Config

options = [
    SelectOption(label="Allowed Admin Roles",
                 value="AllowedAdminRoles",
                 description="Used In: All - which roles are allowed to run all bot commands",
                 emoji="👑"),
    SelectOption(label="Setup User Allowed Channels",
                 value="UserAllowedChannels",
                 description="Limit which channels commands that can be run by anyone are allowed in",
                 emoji="🤖")
]


class SetConfigView(discord.ui.View):
    def __init__(self, embed, msg, bot, guild):
        super().__init__(timeout=None)
        self.msg = msg
        self.embed = embed
        self.bot = bot
        if not hasattr(self, 'responses'):
            self.responses = {}
        self.guild = guild

    @discord.ui.select(options=options, placeholder="Select config...")
    async def on_select(self, interaction, options):
        await interaction.response.defer()
        selected_option = interaction.data['values'][0]

        if selected_option == "AllowedAdminRoles":
            admin_role_ids = Config.select().where((Config.name == "allowed_admin_role_ids") & (Config.guild_id == self.guild.id)).first()
            admin_options = self.role_select(existing=admin_role_ids)

            self.clear_items()
            self.embed.description = ("```Allowed Admin Roles:\nPlease select which roles you would like to give bot "
                                      "access to.```")
            self.add_item(item=discord.ui.Select(placeholder="Select Admin Roles...",
                                                 options=admin_options,
                                                 min_values=0,
                                                 max_values=len(admin_options)))
        elif selected_option == "UserAllowedChannels":
            answer_key = ["leaderboard_channel_ids", "funderboard_channel_ids", "chat_channel_ids"]
            answers = {}
            for index, question in enumerate(settings.SET_USER_CHANNELS, start=0):
                question_view = set_multi_config_view.SetMultiConfigView(config_name=selected_option,
                                                                         question=question,
                                                                         channel=interaction.channel,
                                                                         user=interaction.user,
                                                                         bot=self.bot,
                                                                         guild=self.guild)
                answer = await question_view.send_question(index)
                answers[answer_key[index]] = answer
                if answer == "APPLICATION_CANCEL":
                    break

            await self.handle_multi_question_response(name="user_allowed_channels", answers=answers,
                                                      description="```User Allowed Channels:\nChoose which channels a "
                                                                  "user can interact with the bot in.```",
                                                      guild=self.guild)

        await self.msg.channel.send(embed=self.embed, view=self)

        events = [
            self.bot.wait_for('message',
                         check=lambda inter: inter.author == interaction.user and inter.channel == interaction.channel),
            self.bot.wait_for('interaction',
                         check=lambda inter: inter.user == interaction.user and inter.channel == interaction.channel)
        ]

        # with asyncio.FIRST_COMPLETED, this triggers as soon as one of the events is fired
        done, pending = await asyncio.wait(events, return_when=asyncio.FIRST_COMPLETED)
        event = done.pop().result()
        try:
            await event.response.defer()
        except:
            pass

        # cancel the other check
        for future in pending:
            future.cancel()

        if type(event) == discord.Interaction:
           if selected_option == "AllowedAdminRoles":
                await self.set_generic_role_config(pretty_name=selected_option,
                                                   name="allowed_admin_role_ids",
                                                   event=event,
                                                   guild=self.guild)
        else:
            pass

    async def set_generic_config(self, name=None, value=None, send_response=True, guild=discord.Guild):
        configuration, action = Config.create_or_update(name=name, value=value, guild=guild)
        if not configuration:
            self.embed.color = 0xf23f42
            self.embed.description = "```ERR:\nUnable to create/update config```"
        else:
            self.embed.add_field(name="Action", value=f"`{action}`", inline=False)
            config_value = configuration.get_value()
            if type(config_value) == dict:
                for key, value in config_value.items():
                    formatted_value = value
                    if type(formatted_value) == list:
                        formatted_value = "\n".join([str(v) for v in value])
                    elif type(formatted_value) == dict:
                        formatted_value = ""
                        for k, v in value.items():
                            formatted_value += f"{k}: {v}\n"
                    self.embed.add_field(name=key.title(), value=f"{formatted_value}")
            else:
                self.embed.add_field(name=name.title(), value=f"`{configuration.get_value()}`", inline=True)

        self.clear_items()
        if send_response:
            await self.msg.channel.send(embed=self.embed, view=self)

    async def set_generic_role_config(self, pretty_name=None, name=None, event=None, multi=True, guild=discord.Guild):
        if multi:
            roles = [int(rid) for rid in event.data["values"]]
        else:
            roles = int(event.data["values"][0])

        db_role_ids, action = Config.create_or_update(name=name, value=roles, guild=guild)
        if not db_role_ids:
            self.embed.color = 0xf23f42
            self.embed.description = "```ERR:\nUnable to create/update config```"
        else:
            if multi:
                db_roles = db_role_ids.get_value()
            else:
                db_roles = [db_role_ids.get_value()]
            discord_roles = []
            for role_id in db_roles:
                discord_roles.append(self.guild.get_role(role_id))
            self.embed.add_field(name=pretty_name,
                                 value="\n".join([f"`@{role.name}`" for role in discord_roles]),
                                 inline=True)
            self.embed.add_field(name="Action", value=f"`{action}`", inline=True)
        self.clear_items()
        await self.msg.channel.send(embed=self.embed, view=self)

    async def set_generic_channel_config(self, name=None, value=None, send_response=True, bot=None):
        configuration, action = Config.create_or_update(name=name, value=value)
        if not configuration:
            self.embed.color = 0xf23f42
            self.embed.description = "```ERR:\nUnable to create/update config```"
        else:
            channel = bot.get_channel(configuration.get_value())
            self.embed.add_field(name=name.title(), value=channel.mention, inline=True)
            self.embed.add_field(name="Action", value=f"`{action}`", inline=True)
        self.clear_items()
        if send_response:
            await self.msg.channel.send(embed=self.embed, view=self)

    def role_select(self, existing=None):
        opts = []
        for role in self.guild.roles[-25:]:
            if existing:
                if role.id in existing.value:
                    default = True
                else:
                    default = False
            else:
                default = False
            opts.append(
                discord.SelectOption(
                    label=role.name,
                    value=role.id,
                    default=default
                )
            )
        return list(reversed(opts))

    async def handle_multi_question_response(self, name=None, answers=None, description=None, guild=discord.Guild):
        if answers is None:
            answers = {}
        contains_cancel = "APPLICATION_CANCEL" in answers.values()
        if contains_cancel:
            return
        await self.set_generic_config(name=name,
                                      value=answers,
                                      send_response=False,
                                      guild=guild)
        self.embed.description = description
