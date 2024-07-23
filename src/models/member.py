import pdb
import datetime

import discord
from peewee import *
from playhouse.sqlite_ext import *
from config import settings
from src import helpers
from src.models.base_model import BaseModel
from src.models.guild import Guild
from src.gw2_api_client import GW2ApiClient
from src.lib.logger import logger


class Member(BaseModel):
    username = CharField()
    guild_id = ForeignKeyField(Guild, backref="members")
    discord_id = IntegerField()
    user_id = IntegerField(null=True)
    gw2_api_key = CharField(null=True)
    gw2_stats = JSONField(null=True)
    gw2_username = CharField(null=True)
    created_at = DateTimeField()
    updated_at = DateTimeField(null=True)

    class Meta:
        indexes = (
            (('guild_id', 'discord_id'), True),  # Composite unique index
            (('guild_id', 'username'), True),    # Composite unique index
        )

    @property
    def api_key(self):
        from src.models.api_key import ApiKey
        ak = self.api_keys.where(ApiKey.primary == True).first()
        if ak:
            return ak.value
        else:
            return None

    def api_key_is_leaderboard_enabled(self):
        from src.models.api_key import ApiKey
        ak = self.api_keys.where(ApiKey.primary == True).first()
        if ak:
            return ak.leaderboard_enabled
        else:
            return None

    def list_gw2_api_keys(self):
        return [api_key.value for api_key in self.api_keys]

    def gw2_api_keys(self):
        key_list = []
        for api_key in self.api_keys:
            key_list.append(
                {
                    "name": api_key.name,
                    "value": api_key.value,
                    "primary": api_key.primary
                }
            )
        return key_list

    def total_count(self):
        return self.attendances.count()

    def weekly_kill_count(self):
        if not self.gw2_stats:
            return 0
        return self.gw2_stats["kills"]["this_week"] - self.gw2_stats["kills"]["last_week"]

    def weekly_capture_count(self):
        if not self.gw2_stats:
            return 0
        return self.gw2_stats["captures"]["this_week"] - self.gw2_stats["captures"]["last_week"]

    def weekly_ranks_count(self):
        if not self.gw2_stats:
            return 0
        return self.gw2_stats["wvw_ranks"]["this_week"] - self.gw2_stats["wvw_ranks"]["last_week"]

    def weekly_deaths_count(self):
        if not self.gw2_stats or 'deaths' not in self.gw2_stats:
            return 0
        return self.gw2_stats["deaths"]["this_week"] - self.gw2_stats["deaths"]["last_week"]

    def weekly_kdr(self):
        return helpers.calculate_kd(self.weekly_kill_count(), self.weekly_deaths_count())

    def weekly_supply_spent(self):
        return self.gw2_stats["supply"]["this_week"] - self.gw2_stats["supply"]["last_week"]

    def weekly_yaks_escorted(self):
        return self.gw2_stats["yaks"]["this_week"] - self.gw2_stats["yaks"]["last_week"]

    def gw2_name(self):
        if self.gw2_username:
            return self.gw2_username
        elif self.api_key:
            gw2_username = GW2ApiClient(api_key=self.api_key).account()["name"]
            self.gw2_username = gw2_username
            self.save()
            return gw2_username
        else:
            return ""

    def legendary_spikes(self):
        try:
            return self.gw2_stats["legendary_spikes"]
        except:
            return 0

    def gifts_of_battle(self):
        items = GW2ApiClient(api_key=self.api_key).bank()
        gift_of_battle_id = 19678
        count = 0
        if items:
            for item in items:
                if item["id"] == gift_of_battle_id:
                    count += item["count"]
        return count

    def supply_spent(self):
        repairs = GW2ApiClient(api_key=self.api_key).account_achievements(name="Repair Master")
        return repairs[0]["current"]

    def yak_escorts(self):
        yaks = GW2ApiClient(api_key=self.api_key).account_achievements(name="A Pack Dolyak's Best Friend")
        return yaks[0]["current"]

    def gw2_guild_ids(self):
        gw2_guild_ids = GW2ApiClient(api_key=self.api_key).account()
        if gw2_guild_ids:
            return gw2_guild_ids["guilds"]
        else:
            return []

    def gw2_guild_names(self):
        gw2_guild_ids = self.gw2_guild_ids()
        gw2_guild_names = []
        for guild_id in gw2_guild_ids:
            gw2_guild = GW2ApiClient(api_key=self.api_key, guild_id=guild_id).guild(gw2_guild_id=guild_id)
            full_gw2_guild_name = f"{gw2_guild['name']} [{gw2_guild['tag']}]"
            gw2_guild_names.append(full_gw2_guild_name)
        return gw2_guild_names

    def gw2_guild_tags(self):
        gw2_guild_ids = self.gw2_guild_ids()
        gw2_guild_tags = []
        for guild_id in gw2_guild_ids:
            gw2_guild = GW2ApiClient(api_key=self.api_key, guild_id=guild_id).guild(gw2_guild_id=guild_id)
            gw2_guild_tags.append(gw2_guild['tag'])
        return gw2_guild_tags


    @staticmethod
    def find_or_create(member=discord.Member, guild=discord.Guild):
        db_member = Member.select().where((Member.discord_id == member.id) & (Member.guild_id == guild.id)).first()
        if db_member:
            return db_member
        else:
            return Member.create(
                username=member.name,
                discord_id=member.id,
                guild_id=guild.id,
                created_at=datetime.datetime.now()
            )
