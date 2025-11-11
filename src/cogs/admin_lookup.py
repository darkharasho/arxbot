import pdb
import discord
import json

from discord.ext import commands
from discord import app_commands
from config import settings
from src import helpers
from src import authorization
from tabulate import tabulate
from src.gw2_api_client import GW2ApiClient
from peewee import *
from src.models.member import Member
from src.cogs.stats_cog import StatsCog
from datetime import datetime
from src.db_viewer import DBViewer
from src.lib.smart_embed import SmartEmbed

tabulate.PRESERVE_WHITESPACE = True


WVW_TEAM_NAMES = {
    11001: {"en": "Moogooloo", "de": "Muuguuluu", "es": "Mugulú", "fr": "Moogooloo"},
    11002: {"en": "Rall's Rest", "de": "Ralls Rast", "es": "Descanso de Rall", "fr": "Repos de Rall"},
    11003: {"en": "Domain of Torment", "de": "Domäne der Pein", "es": "Dominio de Tormento", "fr": "Domaine du tourment"},
    11004: {"en": "Yohlon Haven", "de": "Yohlon-Winkel", "es": "Puerto de Yohlon", "fr": "Havre de Yohlon"},
    11005: {"en": "Tombs of Drascir", "de": "Gräber von Drascir", "es": "Tumba de Drascir", "fr": "Tombes de Drascir"},
    11006: {"en": "Hall of Judgment", "de": "Halle des jüngsten Gerichts", "es": "Sala del Juicio", "fr": "Hall de jugement"},
    11007: {"en": "Throne of Balthazar", "de": "Thron des Balthasar", "es": "Trono de Balthazar", "fr": "Trône de Balthazar"},
    11008: {"en": "Dwayna's Temple", "de": "Dwaynas Tempel", "es": "Templo de Dwayna", "fr": "Temple de Dwayna"},
    11009: {"en": "Abaddon's Prison", "de": "Abaddons Gefängnis", "es": "Prisón de Abaddon", "fr": "Prison d'Abaddon"},
    11010: {"en": "Cathedral of Blood", "de": "Kathedrale des Blutes", "es": "Catedral de la Sangre", "fr": "Cathédrale sanglante"},
    11011: {"en": "Lutgardis Conservatory", "de": "Lutgardis-Wintergarten", "es": "Invernadero de Lutgardis", "fr": "Conservatoire de Lutgardis"},
    11012: {"en": "Mosswood", "de": "Mooswald", "es": "Bosquemusgoso", "fr": "Bois moussu"},
    12001: {"en": "Skrittsburgh", "de": "Skrittsburg", "es": "Skrittsburgo", "fr": "Skrittsburgh"},
    12002: {"en": "Fortune's Vale", "de": "Glückstal", "es": "Valle de la Fortuna", "fr": "Vallée de la fortune"},
    12003: {"en": "Silent Woods", "de": "Stille Wälder", "es": "Bosques Silenciosos", "fr": "Forêt silencieuse"},
    12004: {"en": "Ettin's Back", "de": "Ettinbuckel", "es": "Loma de Ettin", "fr": "Échine d'Ettin"},
    12005: {"en": "Domain of Anguish", "de": "Domäne der Seelenpein", "es": "Dominio de la Angustia", "fr": "Domaine de l'angoisse"},
    12006: {"en": "Palawadan", "de": "Palawadan", "es": "Palawadan", "fr": "Palawadan"},
    12007: {"en": "Bloodstone Gulch", "de": "Blutstein-Schlucht", "es": "Barranco de Hematites", "fr": "Ravn de la pierre de sang"},
    12008: {"en": "Frost Citadel", "de": "Frostzitadelle", "es": "Ciudadela de la Escarcha", "fr": "Citadelle du givre"},
    12009: {"en": "Dragrimmar", "de": "Dragrimmar", "es": "Dragrimmar", "fr": "Dragrimmar"},
    12010: {"en": "Grenth's Door", "de": "Grenths Tür", "es": "Puerta de Grenth", "fr": "Porte de Grenth"},
    12011: {"en": "Mirror of Lyssa", "de": "Spiegel der Lyssa", "es": "Espejo de Lyssa", "fr": "Miroir de Lyssa"},
    12012: {"en": "Melandru's Dome", "de": "Melandrus-Dom", "es": "Cúpula de Melandru", "fr": "Dôme de Melandru"},
    12013: {"en": "Kormir's Library", "de": "Kormirs Bibliothek", "es": "Biblioteca de Kormir", "fr": "Bibliothèque de Kormir"},
    12014: {"en": "Great House Aviary", "de": "Vogelhalle des Groẞen Hauses", "es": "Gran Aviario", "fr": "Volière de la grande maison"},
    12015: {"en": "Bava Nisos", "de": "Bava Nisos", "es": "Bava Nisos", "fr": "Bava Nisos"},
}


class AdminLookup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def _format_wvw_team_details(team_id):
        if team_id is None:
            return "WvW Team: Unknown"

        try:
            team_id_int = int(team_id)
        except (TypeError, ValueError):
            return f"WvW Team ID: {team_id}"

        team_names = WVW_TEAM_NAMES.get(team_id_int)
        team_name = None
        if isinstance(team_names, dict):
            raw_name = team_names.get("en")
            if isinstance(raw_name, str):
                team_name = raw_name.strip()

        if team_name:
            return f"WvW Team: {team_name} ({team_id_int})"

        return f"WvW Team ID: {team_id_int}"

    def model_to_dict(self, model):
        """Convert a Peewee model instance to a dictionary."""
        return {
            'value': model.value,
            'name': model.name,
            'primary': model.primary
        }

    @app_commands.command(
        name="admin_lookup",
        description="Admin: Tie Discord and Guild Wars 2 data together"
    )
    async def admin_lookup(self, interaction: discord.Interaction, member: discord.Member):
        if await authorization.ensure_admin(interaction):
            await interaction.response.defer(ephemeral=True)
            db_member = Member.find_or_create(member=member, guild=interaction.guild)

            embed = discord.Embed(title=f"{member.display_name} | {member.name}", description="")
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="", value="```------ Account Details ------```", inline=False)

            if len(db_member.api_keys) > 0:
                embed.add_field(name="Guilds", value=f"```- " + '\n- '.join(db_member.gw2_guild_names()) + "```",
                                inline=False)

                gw2_account_blocks = []
                for api_key in db_member.api_keys:
                    api_client = GW2ApiClient(api_key=api_key.value)
                    try:
                        account_details = api_client.account()
                    except Exception:
                        account_details = None

                    account_lines = [f"- {api_key.name}"]
                    detail_parts = []

                    if account_details:
                        wvw_rank = account_details.get("wvw_rank")
                        if wvw_rank is not None:
                            detail_parts.append(f"WvW Rank: {wvw_rank}")

                        commander_tag = account_details.get("commander")
                        if commander_tag is not None:
                            detail_parts.append(f"Commander: {'Yes' if commander_tag else 'No'}")

                        team_id = account_details.get("wvw_team")
                        if team_id:
                            detail_parts.append(self._format_wvw_team_details(team_id))

                    if detail_parts:
                        account_lines.extend([f"    {part}" for part in detail_parts])
                    elif account_details is None:
                        account_lines.append("    Unable to fetch account details")

                    gw2_account_blocks.append("\n".join(account_lines))

                embed.add_field(name="GW2 Accounts", value="```" + "\n\n".join(gw2_account_blocks) + "```",
                                inline=False)
            else:
                embed.add_field(name="API Keys", value="```No API Keys found```", inline=False)
            await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    for guild in bot.guilds:
        await bot.add_cog(AdminLookup(bot), guild=guild, override=True)
