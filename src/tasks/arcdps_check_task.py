import requests

import discord
import requests
from datetime import datetime, timedelta, timezone
from discord.ext import commands, tasks
from config import settings
from src.lib.logger import logger
from src.models.config import Config
from src import helpers
from bs4 import BeautifulSoup


class ArcDpsCheckTask(commands.Cog):
    def __init__(self, bot):
        self.url = "https://www.deltaconnected.com/arcdps/x64/"
        self.bot = bot
        self.arcdps_check.start()

    def cog_unload(self):
        self.arcdps_check.cancel()

    # @tasks.loop(seconds=60000)
    @tasks.loop(minutes=15.0)
    async def arcdps_check(self):
        for guild in self.bot.guilds:
            if Config.arcdps_updates(guild_id=guild.id) and Config.arcdps_updates(nested_cfg=["enabled"]):
                response = requests.get(self.url)
                parsed_html = BeautifulSoup(response.text, features="html.parser")
                last_updated_at_str = (parsed_html.body.find('tr', attrs={'class': 'odd'}).
                                       find('td', attrs={'class': 'indexcollastmod'}).text)
                last_updated_at = datetime.datetime.strptime(last_updated_at_str.strip(), "%Y-%m-%d %H:%M")
                utc_updated_at = pytz.UTC.localize(last_updated_at)
                local_updated_at = utc_updated_at.astimezone(tzlocal.get_localzone())
                db_arcdps = ArcDPS.get_last_updated()

                if db_arcdps:
                    if last_updated_at > db_arcdps.last_updated_at:
                        ArcDPS.update(last_updated_at=last_updated_at).where(ArcDPS.id == db_arcdps.id).execute()
                        arctuple = int(time.mktime(local_updated_at.timetuple()))

                        embed = discord.Embed(
                            title="ArcDPS Update",
                            description="",
                            color=0xffdb5a)
                        embed.set_author(name=f"{settings.GUILD} - ArcDPS Releases", icon_url=self.guild.icon.url)
                        embed.add_field(name="Last Updated", value=f"**<t:{arctuple}:R>**")
                        embed.add_field(name="Date & Time", value=f"**<t:{arctuple}:f>**")
                        embed.add_field(name="⚔️ Download", value=f"[arcdps](https://www.deltaconnected.com/arcdps/x64/)", inline=False)

                        file_name = helpers.select_icon("Legendary_Insight")
                        file = discord.File(file_name)
                        embed.set_thumbnail(url=f"attachment://{file.filename}")

                        channel = self.guild.get_channel(Config.arcdps_updates(nested_cfg=["channel_id"]))
                        await channel.send(embed=embed, file=file)
                    print(f"[ARCDPS UPDATES]".ljust(20) + f"⚔️ Checked at {db_arcdps.last_updated_at}")
                else:
                    ArcDPS.create(last_updated_at=last_updated_at)


async def setup(bot):
    for guild in bot.guilds:
        await bot.add_cog(ArcDpsCheckTask(bot), guild=guild, override=True)
