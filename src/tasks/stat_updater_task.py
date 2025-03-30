import discord
import datetime
import asyncio
from discord.ext import commands, tasks
from config import settings
from src.gw2_api_client import GW2ApiClient
from src.models.member import Member
from src.models.api_key import ApiKey
from src.lib.logger import logger


class StatUpdaterTask(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_stats.start()

    def cog_unload(self):
        self.update_stats.cancel()

    @tasks.loop(minutes=45.0)
    async def update_stats(self):
        logger.info("[GW2 SYNC] 🟢 STARTED")
        await self.bulk_update()
        logger.info("[GW2 SYNC] 🟢 DONE")

    async def bulk_update(self):
        guild = self.bot.get_guild(settings.GUILD_ID)  # Replace with your guild ID
        if not guild:
            logger.error("[GW2 SYNC] 🔴 Guild not found. Check GUILD_ID in settings.")
            return

        # Prefetch all members with their roles
        all_members = {member.id: member for member in guild.members if "Alliance Member" in [role.name for role in member.roles]}
        members = list(set([api_key.member for api_key in ApiKey.select().where(ApiKey.leaderboard_enabled == True)]))
        total_members = len(members)

        for index, member in enumerate(members, start=1):
            if member.discord_id not in all_members:
                logger.info(f"[GW2 SYNC] ⚪ Skipping {member.username} (not an Alliance Member)")
                continue

            start_time = datetime.datetime.now()
            try:
                # Run all stat updates in parallel for the member
                await asyncio.gather(
                    self.update_kill_count(member),
                    self.update_capture_count(member),
                    self.update_rank_count(member),
                    self.update_deaths_count(member),
                    self.update_supply_spent(member),
                    self.update_yaks_escorted(member),
                    self.update_spikes(member),
                )
                logger.info(f"[GW2 SYNC] 🟢 ({index}/{total_members}) {member.username}: {datetime.datetime.now() - start_time}")
            except Exception as e:
                logger.error(f"[GW2 SYNC] 🔴 ({index}/{total_members}) {member.username}: {datetime.datetime.now() - start_time}")
                logger.error(f"    [ERR] {e}")

    async def update_kill_count(self, member):
        try:
            kills = 0
            for api_key in member.api_keys:
                avenger_stats = await GW2ApiClient(api_key=api_key.value).aio_account_achievements(name="Realm Avenger")
                if avenger_stats:
                    kills += avenger_stats[0]["current"]
            await self.update_stat(member, "kills", kills)
        except Exception as e:
            logger.error(f"    [ERR] Failed to update kills for {member.username}: {e}")

    async def update_capture_count(self, member):
        try:
            captures = 0
            for api_key in member.api_keys:
                conqueror = await GW2ApiClient(api_key=api_key.value).aio_account_achievements(name="Emblem of the Conqueror")
                if conqueror:
                    captures += conqueror[0].get("current", 0) + (conqueror[0].get("repeated", 0) * 100)
            await self.update_stat(member, "captures", captures)
        except Exception as e:
            logger.error(f"    [ERR] Failed to update captures for {member.username}: {e}")

    async def update_rank_count(self, member):
        try:
            wvw_ranks = 0
            for api_key in member.api_keys:
                account = await GW2ApiClient(api_key=api_key.value).aio_account()
                if account:
                    wvw_ranks += account["wvw"]["rank"]
            await self.update_stat(member, "wvw_ranks", wvw_ranks)
        except Exception as e:
            logger.error(f"    [ERR] Failed to update ranks for {member.username}: {e}")

    async def update_deaths_count(self, member):
        try:
            deaths = 0
            for api_key in member.api_keys:
                characters = await GW2ApiClient(api_key=api_key.value).aio_characters(ids="all")
                if characters:
                    for character in characters:
                        deaths += character["deaths"]
            await self.update_stat(member, "deaths", deaths)
        except Exception as e:
            logger.error(f"    [ERR] Failed to update deaths for {member.username}: {e}")

    async def update_supply_spent(self, member):
        try:
            supply = 0
            for api_key in member.api_keys:
                repair_master = await GW2ApiClient(api_key=api_key.value).aio_account_achievements(name="Repair Master")
                if repair_master:
                    supply += repair_master[0]["current"]
            await self.update_stat(member, "supply", supply)
        except Exception as e:
            logger.error(f"    [ERR] Failed to update supply for {member.username}: {e}")

    async def update_yaks_escorted(self, member):
        try:
            yaks = 0
            for api_key in member.api_keys:
                yak_escorts = await GW2ApiClient(api_key=api_key.value).aio_account_achievements(name="A Pack Dolyak's Best Friend")
                if yak_escorts:
                    yaks += yak_escorts[0]["current"]
            await self.update_stat(member, "yaks", yaks)
        except Exception as e:
            logger.error(f"    [ERR] Failed to update yaks for {member.username}: {e}")

    async def update_spikes(self, member):
        try:
            count = 0
            legendary_spike_id = 81296
            for api_key in member.api_keys:
                items = api_key.api_client().bank()
                if items:
                    for item in items:
                        if item["id"] == legendary_spike_id:
                            count += item["count"]
            await self.update_stat(member, "legendary_spikes", count, single_mode=True)
        except Exception as e:
            logger.error(f"    [ERR] Failed to update spikes for {member.username}: {e}")

    @staticmethod
    async def update_stat(member, stat_name, stat, single_mode=False):
        try:
            stats = member.gw2_stats or {}
            if single_mode:
                stats[stat_name] = stat
            else:
                stats[stat_name] = {
                    "last_week": stats.get(stat_name, {}).get("this_week", 0),
                    "this_week": stat,
                }
            Member.update(gw2_stats=stats, updated_at=datetime.datetime.now()).where(Member.id == member.id).execute()
        except Exception as e:
            logger.error(f"    [ERR] Failed to update database for {member.username} ({stat_name}): {e}")


async def setup(bot):
    await bot.add_cog(StatUpdaterTask(bot))
