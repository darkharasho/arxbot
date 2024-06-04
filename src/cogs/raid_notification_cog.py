import pdb

import discord

from discord.ext import commands
from discord import app_commands
from config import settings
from src import helpers
from src import authorization
from tabulate import tabulate
from src.gw2_api_client import GW2ApiClient
from src.models.member import Member
tabulate.PRESERVE_WHITESPACE = True


class RaidNotificationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="raid-notification",
        description="Announce a raid on a map"
    )
    @app_commands.choices(wvw_map=[
        app_commands.Choice(name='⚔️ ⚪ Eternal Battlegrounds', value='Eternal Battlegrounds'),
        app_commands.Choice(name='⚔️ 🟢 Green Alpine Borderlands', value='Green Alpine Borderlands'),
        app_commands.Choice(name='⚔️ 🔵 Blue Alpine Borderlands', value='Blue Alpine Borderlands'),
        app_commands.Choice(name='⚔️ 🔴 Red Desert Borderlands', value='Red Desert Borderlands')
    ])
    async def raid_notification(self, interaction, wvw_map: str, channel: discord.TextChannel, role_pings: str):
        await interaction.response.defer(ephemeral=True)

        role_ids = [int(role_id.strip("<@&>")) for role_id in role_pings.split()]
        roles = [interaction.guild.get_role(role_id) for role_id in role_ids if interaction.guild.get_role(role_id)]
        member = Member.select().where(Member.discord_id == interaction.user.id).first()

        if member is None:
            embed = discord.Embed(
                title="Failed to Post Notification",
                description=f"No API key found for your user",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)
            return
        elif member.api_key is None:
            embed = discord.Embed(
                title="Failed to Post Notification",
                description=f"No API key found for your user",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)
            return

        gw2_api_client = GW2ApiClient(api_key=member.api_key)
        wvw_maps = gw2_api_client.wvw_maps()
        wvw_matches = gw2_api_client.wvw_matches()

        ping_body = ""
        for role in roles:
            ping_body += f"{role.mention} "

        if "Eternal" in wvw_map:
            banner_file_name = helpers.select_icon("Eternal_Battlegrounds_loading_screen", file_type="jpg")
            color = 0xffffff
            thumbnail_file_name = helpers.select_icon("Commander_tag_white")
            body = "# ⚔️ Tagging Up, EBG!\n"
            body += f"### Map\nEternal Battlegrounds\n"
        elif "Green" in wvw_map:
            banner_file_name = helpers.select_icon("Green_Borderlands_loading_screen", file_type="jpg")
            color = 0x1c9b1c
            thumbnail_file_name = helpers.select_icon("Commander_tag_green")

            body = "# ⚔️ Tagging Up, Green BL!\n"
            world_id = wvw_maps["worlds"]["green"]
            world = gw2_api_client.cached_find_world_by_id(world_id)
            body += f"### Map\n{world['name']} Alpine Borderlands\n"
        elif "Blue" in wvw_map:
            banner_file_name = helpers.select_icon("Blue_Borderlands_loading_screen", file_type="jpg")
            color = 0x0d4d6f
            thumbnail_file_name = helpers.select_icon("Commander_tag_blue")

            body = "# ⚔️ Tagging Up, Blue BL!\n"
            world_id = wvw_maps["worlds"]["blue"]
            world = gw2_api_client.cached_find_world_by_id(world_id)
            body += f"### Map\n{world['name']} Alpine Borderlands\n"
        elif "Red" in wvw_map:
            banner_file_name = helpers.select_icon("Red_Borderlands_loading_screen", file_type="jpg")
            color = 0xc20b08
            thumbnail_file_name = helpers.select_icon("Commander_tag_red")

            body = "# ⚔️ Tagging Up, Red BL!\n"
            world_id = wvw_maps["worlds"]["red"]
            world = gw2_api_client.cached_find_world_by_id(world_id)
            body += f"### Map\n{world['name']} Desert Borderlands\n"

        scores = wvw_matches["scores"]
        victory_points = wvw_matches["victory_points"]
        kills = wvw_matches["kills"]
        deaths = wvw_matches["deaths"]
        scores_list = []
        for score_key, score_value in scores.items():
            world = gw2_api_client.cached_find_world_by_id(wvw_maps["worlds"][score_key])
            abbr_world_name = helpers.abbreviate_world_name(world["name"])
            if score_key == "blue":
                world_color = "🟦"
            elif score_key == "green":
                world_color = "🟩"
            elif score_key == "red":
                world_color = "🟥"

            kd = helpers.calculate_kd(kills[score_key], deaths[score_key])

            scores_list.append([
                f"{world_color}{abbr_world_name}",
                victory_points[score_key],
                kd
            ])
        sorted_scores_list = sorted(scores_list, key=lambda x: x[1], reverse=True)
        tablefmt = "plain"
        headers = ["⬛Team", "VPs", "KDR"]
        table = tabulate(sorted_scores_list, headers, tablefmt=tablefmt, showindex=["1st", "2nd", "3rd"])

        body += f"### Scores\n```{table}```"

        raid_embed = discord.Embed(title="", description=body, color=color)
        raid_embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon.url)

        banner_file = discord.File(banner_file_name)
        raid_embed.set_image(url=f"attachment://{banner_file.filename}")

        thumbnail_file = discord.File(thumbnail_file_name)
        raid_embed.set_thumbnail(url=f"attachment://{thumbnail_file.filename}")

        try:
            await channel.send(ping_body, embed=raid_embed, files=[thumbnail_file, banner_file])
            embed = discord.Embed(
                title="Successfully Posted Notification",
                description=f"**Map:** {wvw_map}\n**Channel:** {channel.mention}",
                color=0x0ff000
            )
        except Exception as e:
            embed = discord.Embed(
                title="Failed to Post Notification",
                description=f"**Map:** {wvw_map}\n**Channel:** {channel.mention}\n```{e}```",
                color=0xff0000
            )

        await interaction.followup.send(embed=embed)


async def setup(bot):
    for guild in bot.guilds:
        await bot.add_cog(RaidNotificationCog(bot), guild=guild, override=True)
