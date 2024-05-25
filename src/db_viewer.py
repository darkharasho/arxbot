from discord.ext import commands
from config import settings
from tabulate import tabulate
from peewee import *

from src.models.guild import Guild
from src.models.member import Member
from src.models.api_key import ApiKey


class DBViewer:

    def __init__(self, return_string=False):
        self.db = SqliteDatabase('arxbot.db')
        self.return_string = return_string

    def member(self, member: Member):
        member_data = [
            [
                member.id,
                member.username,
                member.created_at,
                member.updated_at,
                member.guild_id,
                member.discord_id,
                json.dumps(member.gw2_api_keys(), indent=4),
                json.dumps(member.gw2_stats, indent=4)
            ]
        ]
        member_headers = ["ID", "Username", "Created At", "Updated At", "GuildID", "DiscordID", "GW2 API Key", "GW2 Stats"]

        table = tabulate(
            member_data,
            member_headers,
            tablefmt="psql"
        )
        if self.return_string:
            mdata = {}
            for index, mheader in enumerate(member_headers):
                mdata[mheader] = member_data[0][index]
            return mdata
        else:
            print(table)

    # def config(self, config: Config):
    #     config_data = [
    #         [
    #             config.id,
    #             config.name,
    #             config.guild_id,
    #             json.dumps(config.value, indent=4),
    #             config.value_type
    #         ]
    #     ]
    #     config_headers = ["ID", "Name", "GuildID", "Value", "Value Type"]
    #
    #     table = tabulate(
    #         config_data,
    #         config_headers,
    #         tablefmt="psql"
    #     )
    #
    #     if self.return_string:
    #         cdata = {}
    #         for index, cheader in enumerate(config_headers):
    #             cdata[cheader] = config_data[0][index]
    #         return cdata
    #     else:
    #         print(table)
    #
    # def configs(self):
    #     configs = Config.select()
    #     config_data = []
    #     for cfg in configs:
    #         config_data.append(
    #             [
    #                 cfg.id,
    #                 cfg.name,
    #                 cfg.guild_id,
    #                 json.dumps(cfg.value, indent=4),
    #                 cfg.value_type
    #             ]
    #         )
    #     config_headers = ["ID", "Name", "GuildID", "Value", "Value Type"]
    #
    #     table = tabulate(
    #         config_data,
    #         config_headers,
    #         tablefmt="psql"
    #     )
    #
    #     if self.return_string:
    #         return table
    #     else:
    #         print(table)

    def members(self):
        members = Member.select()
        member_data = []
        for mem in members:
            member_data.append(
                [
                    mem.id,
                    mem.username,
                    mem.created_at,
                    mem.updated_at,
                    mem.guild_id,
                    mem.discord_id,
                    json.dumps(mem.gw2_api_keys(), indent=4),
                    json.dumps(mem.gw2_stats, indent=4)
                ]
            )
        member_headers = ["ID", "Username", "Created At", "Updated At", "GuildID", "DiscordID", "GW2 API Key", "GW2 Stats"]

        table = tabulate(
            member_data,
            member_headers,
            tablefmt="psql"
        )

        if self.return_string:
            return member_data
        else:
            print(table)


    def guilds(self):
        guilds = Guild.select()
        guild_data = []
        for guild in guilds:
            guild_data.append(
                [
                    guild.id,
                    guild.name,
                    guild.guild_id
                ]
            )
        guild_headers = ["ID", "Name", "Guild ID"]

        table = tabulate(
            guild_data,
            guild_headers,
            tablefmt="psql"
        )

        if self.return_string:
            return guild_data
        else:
            print(table)
