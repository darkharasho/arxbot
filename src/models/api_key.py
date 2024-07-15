import pdb

import discord
from peewee import *
from playhouse.sqlite_ext import *
from src.models.base_model import BaseModel
from src.models.member import Member
from src.models.guild import Guild
from src.gw2_api_client import GW2ApiClient


class ApiKey(BaseModel):
    member = ForeignKeyField(Member, backref="api_keys")
    value = CharField(unique=True)
    name = TextField(null=False, default="Default")
    primary = BooleanField(default=True)
    guild_id = ForeignKeyField(Guild, null=True, backref="api_keys")
    leaderboard_enabled = BooleanField(default=True)

    def account_id(self):
        return GW2ApiClient(api_key=self.value).account()["id"]

    def api_client(self):
        return GW2ApiClient(api_key=self.value)

    @staticmethod
    def find_or_create(member=discord.Member, value=None, primary=None, leaderboard_enabled=None, guild_id=None):
        api_key = ApiKey.select().where((ApiKey.member == member) & (ApiKey.value == value)).first()
        if api_key:
            return api_key
        else:
            return ApiKey.create(
                member=member,
                name=GW2ApiClient(api_key=value).account()["name"],
                value=value,
                leaderboard_enabled=leaderboard_enabled,
                guild_id=guild_id,
                primary=primary
            )
