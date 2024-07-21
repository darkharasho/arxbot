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
from src.gw2_api_client import GW2ApiClient
from src.lib.smart_embed import SmartEmbed


options = [
    SelectOption(label="Allowed Admin Roles",
                 value="AllowedAdminRoles",
                 description="Used In: All - which roles are allowed to run all bot commands",
                 emoji="👑"),
    SelectOption(label="Temporary Voice Channel Visibility",
                 value="TmpVCVisibility",
                 description="Role allowed to see temporary voice channels, but not connect",
                 emoji="🎙️"),
    SelectOption(label="Clean Channel",
                 value="CleanChannel",
                 description="Deletes messages older than 1 week in a set channel",
                 emoji="🧼"),
    SelectOption(label="Guild Verification",
                 value="GuildVerification",
                 description="Guild roles to assign to members who have added an API Key",
                 emoji="🛡️"),
    SelectOption(label="Setup ArcDPS Updates",
                 value="ArcdpsUpdates",
                 description="Sets up automatic notifications for ArcDPS updates",
                 emoji="🧮"),
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
        elif selected_option == "TmpVCVisibility":
            view_tmp_vc_role = Config.select().where((Config.name == "view_tmp_vc_role_ids") & (Config.guild_id == self.guild.id)).first()
            tmp_vc_options = self.role_select(existing=view_tmp_vc_role)

            self.clear_items()
            self.embed.description = ("```Temporary Voice Channel Visibility:\nPlease select which roles will be able to view but not connect to temporary voice channels.```")
            self.add_item(item=discord.ui.Select(placeholder="Select Temp VC Visibility Roles...",
                                                 options=tmp_vc_options,
                                                 min_values=0,
                                                 max_values=len(tmp_vc_options)))
        elif selected_option == "CleanChannel":
            answer_key = ['channel_id', 'enabled']
            answers = {}
            for index, question in enumerate(settings.SET_CLEAN_CHANNEL, start=0):
                question_view = set_multi_config_view.SetMultiConfigView(config_name=selected_option,
                                                                         question=question,
                                                                         channel=interaction.channel,
                                                                         guild=self.guild,
                                                                         bot=self.bot,
                                                                         user=interaction.user)
                answer = await question_view.send_question(index)
                answers[answer_key[index]] = answer
                if answer == "APPLICATION_CANCEL":
                    break

            self.clear_items()
            await self.handle_multi_question_response(name="clean_channel", answers=answers,
                                                      description="```Clean Channel:\nDelete messages > 1 week.```",
                                                      guild=self.guild)

        elif selected_option == "GuildVerification":
            answer_key = ["gw2_to_discord_mapping", "allowed_roles", "additional_roles"]
            answers = {}
            for index, question in enumerate(settings.SET_VERIFICATION, start=0):
                question_view = set_multi_config_view.SetMultiConfigView(config_name=selected_option,
                                                                         question=question,
                                                                         channel=interaction.channel,
                                                                         guild=self.guild,
                                                                         bot=self.bot,
                                                                         user=interaction.user)
                answer = await question_view.send_question(index)
                if answer_key[index] == "gw2_to_discord_mapping":
                    # Call gw2 api guild search and convert name -> id
                    guild_name_and_ids = []
                    for guild_mapping in answer.split(','):
                        guild_name, guild_tag, discord_role_name = guild_mapping.split('|')

                        # Trim whitespace from the guild_name and discord_role_name
                        guild_name = guild_name.strip()
                        discord_role_name = discord_role_name.strip()

                        # Search for the guild ID using the trimmed guild_name
                        guild_id = GW2ApiClient().guild_search(guild_name=guild_name)

                        # Search for the role in the guild, ignoring case
                        discord_role = next(
                            (r for r in self.guild.roles if r.name.lower() == discord_role_name.lower()), None)

                        if len(guild_id) > 0 and discord_role:
                            gw2_guild = GW2ApiClient().guild(gw2_guild_id=guild_id[0], auth=False)
                            guild_name_and_ids.append(
                                {
                                    "guild_id": gw2_guild["id"],
                                    "guild_name": gw2_guild["name"],
                                    "guild_tag": gw2_guild["tag"],
                                    "discord_role_id": discord_role.id
                                }
                            )
                    answers[answer_key[index]] = guild_name_and_ids
                else:
                    answers[answer_key[index]] = answer
                if answer == "APPLICATION_CANCEL":
                    break

            self.clear_items()
            await self.handle_multi_question_response(name="guild_verification", answers=answers,
                                                      description="```Guild Verification:\nAuto role on gw2 guild verify.```",
                                                      guild=self.guild)
        elif selected_option == "ArcdpsUpdates":
            answer_key = ["enabled", "channel_id"]
            answers = {}
            for index, question in enumerate(settings.SET_ARCDPS_UPDATES, start=0):
                question_view = set_multi_config_view.SetMultiConfigView(config_name=selected_option,
                                                                         question=question,
                                                                         channel=interaction.channel,
                                                                         user=interaction.user)
                answer = await question_view.send_question(index)
                answers[answer_key[index]] = answer
                if answer == "APPLICATION_CANCEL":
                    break

            self.clear_items()
            await self.set_generic_config(name="arcdps_updates",
                                          value=answers,
                                          send_response=False)
            try:
                await bot.reload_extension("src.cogs.arcdps_updates_cog")
            except:
                pass

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
           elif selected_option == "TmpVCVisibility":
               await self.set_generic_role_config(pretty_name=selected_option,
                                                  name="view_tmp_vc_role_ids",
                                                  event=event,
                                                  guild=self.guild)
        else:
            pass

    async def set_generic_config(self, name=None, value=None, send_response=True, guild=discord.Guild):
        configuration, action = Config.create_or_update(name=name, value=value, guild=guild)
        embed = SmartEmbed(title="Configuration Update")

        if not configuration:
            embed.color = 0xf23f42
            embed.description = "```ERR:\nUnable to create/update config```"
        else:
            embed.add_field(name="Action", value=f"`{action}`", inline=False)

            config_value = configuration.get_value()
            if isinstance(config_value, dict):
                for key, value in config_value.items():
                    if isinstance(value, list):
                        formatted_value = "\n".join([str(v) for v in value])
                        embed.add_field(name=key.title(), value=formatted_value, value_type="dict", inline=False)
                    elif isinstance(value, dict):
                        embed.add_field(name=key.title(), value=value, value_type="dict", inline=False)
                    else:
                        embed.add_field(name=key.title(), value=str(value), value_type="string", inline=False)
            else:
                shortened_value = configuration.get_value()[:800]
                embed.add_field(name=name.title(), value=f"`{shortened_value}`", value_type="string", inline=True)

        embeds = embed.create_embeds()

        self.clear_items()
        if send_response:
            for emb in embeds:
                await self.msg.channel.send(embed=emb, view=self)

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
                                      send_response=True,
                                      guild=guild)
        self.embed.description = description
