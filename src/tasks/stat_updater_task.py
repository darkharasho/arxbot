import discord
import requests
import datetime
from discord.ext import commands, tasks
from config import settings
from src.gw2_api_client import GW2ApiClient
from src.models.member import Member
from src.models.api_key import ApiKey


class StatUpdaterTask(commands.Cog):
    def __init__(self, bot, api_key=None):
        self.bot = bot
        self.update_stats.start()

    def cog_unload(self):
        self.update_stats.cancel()

    # @tasks.loop(seconds=60000)
    @tasks.loop(minutes=45.0)
    async def update_stats(self):
        await self.bulk_update()

    async def bulk_update(self):
        logger.info("[GW2 SYNC]".ljust(20) + f"🟢 STARTED")
        members = list(set([api_key.member for api_key in ApiKey.select().where(ApiKey.leaderboard_enabled == True)]))
        progress = {
            "kills": False,
            "captures": False,
            "ranks": False,
            "deaths": False,
            "supply": False,
            "yaks": False,
            "spikes": False
        }

        for index, member in enumerate(members, start=1):
            try:
                start_time = datetime.datetime.now()
                await self.update_kill_count(member)
                progress["kills"] = True
                await self.update_capture_count(member)
                progress["captures"] = True
                await self.update_rank_count(member)
                progress["ranks"] = True
                await self.update_deaths_count(member)
                progress["deaths"] = True
                await self.update_supply_spent(member)
                progress["supply"] = True
                await self.update_yaks_escorted(member)
                progress["yaks"] = True
                await self.update_spikes(member)
                progress["spikes"] = True
                logger.info("[GW2 SYNC]".ljust(20) + f"🟢 ({index}/{len(members)}) {member.username}: {datetime.datetime.now() - start_time}")
            except Exception as e:
                logger.info("[GW2 SYNC]".ljust(20) + f"🔴 ({index}/{len(members)}) {member.username}: {datetime.datetime.now() - start_time}")
                logger.info(" ".ljust(23) + f"[ERR] {e}")
                logger.info(" ".ljust(23) + f"[PROGRESS] {progress}")

        logger.info("[GW2 SYNC]".ljust(20) + f"🟢 DONE")

    async def update_kill_count(self, member):
        member = Member.get(Member.id == member.id)
        kills = 0
        for api_key in member.api_keys:
            avenger_stats = GW2ApiClient(api_key=api_key.value).account_achievements(name="Realm Avenger")
            if avenger_stats:
                kills += avenger_stats[0]["current"]
        await self.update(member=member, stat_name="kills", stat=kills)

    async def update_capture_count(self, member):
        member = Member.get(Member.id == member.id)
        captures = 0
        for api_key in member.api_keys:
            conqueror = GW2ApiClient(api_key=api_key.value).account_achievements(name="Emblem of the Conqueror")
            if conqueror:
                captures += conqueror[0].get("current", 0) + (conqueror[0].get("repeated", 0) * 100)
        await self.update(member=member, stat_name="captures", stat=captures)

    async def update_rank_count(self, member):
        member = Member.get(Member.id == member.id)
        wvw_ranks = 0
        for api_key in member.api_keys:
            account = await GW2ApiClient(api_key=api_key.value).aio_account()
            if account:
                wvw_ranks += account["wvw"]["rank"]
        await self.update(member=member, stat_name="wvw_ranks", stat=wvw_ranks)

    async def update_deaths_count(self, member):
        member = Member.get(Member.id == member.id)
        deaths = 0
        for api_key in member.api_keys:
            characters = GW2ApiClient(api_key=api_key.value).characters(ids="all")
            if characters:
                for character in characters:
                    deaths += character["deaths"]
        await self.update(member=member, stat_name="deaths", stat=deaths)

    async def update_supply_spent(self, member):
        member = Member.get(Member.id == member.id)
        supply = 0
        for api_key in member.api_keys:
            repair_master = GW2ApiClient(api_key=api_key.value).account_achievements(name="Repair Master")
            if repair_master:
                supply += repair_master[0]["current"]
        await self.update(member=member, stat_name="supply", stat=supply)

    async def update_yaks_escorted(self, member):
        member = Member.get(Member.id == member.id)
        yaks = 0
        for api_key in member.api_keys:
            yak_escorts = GW2ApiClient(api_key=api_key.value).account_achievements(name="A Pack Dolyak's Best Friend")
            if yak_escorts:
                yaks += yak_escorts[0]["current"]
        await self.update(member=member, stat_name="yaks", stat=yaks)

    async def update_spikes(self, member):
        member = Member.get(Member.id == member.id)
        count = 0
        legendary_spike_id = 81296
        for api_key in member.api_keys:
            items = api_key.api_client().bank()

            if items:
                for item in items:
                    if item["id"] == legendary_spike_id:
                        count += item["count"]
        await self.update(member=member, stat_name="legendary_spikes", stat=count, single_mode=True)

    @staticmethod
    async def update(member=Member, stat_name=None, stat=None, single_mode=False):
        if single_mode:
            stats = member.gw2_stats
            stats[stat_name] = stat
        else:
            if member.gw2_stats and member.gw2_stats.get(stat_name, None):
                stats = member.gw2_stats
                stats[stat_name]["this_week"] = stat

                # Check if it's reset to update "last_week" data
                current_time_utc = datetime.datetime.utcnow()
                current_time_utc_minus_7 = current_time_utc - datetime.timedelta(hours=7)
                if current_time_utc_minus_7.weekday() == 4 and current_time_utc_minus_7.hour == 17:
                    stats[stat_name]["last_week"] = stat
            else:
                stats = member.gw2_stats or {}
                stats[stat_name] = {
                    "last_week": stat,
                    "this_week": stat
                }
        try:
            Member.update(gw2_stats=stats, updated_at=datetime.datetime.now()).where(Member.id == member.id).execute()
        except:
            sleep(3)
            Member.update(gw2_stats=stats, updated_at=datetime.datetime.now()).where(Member.id == member.id).execute()


async def setup(bot):
    for guild in bot.guilds:
        await bot.add_cog(StatUpdaterTask(bot), guild=guild, override=True)
