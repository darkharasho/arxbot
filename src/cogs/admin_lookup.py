import pdb
import discord

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
    def _format_wvw_team_name(team_id):
        if team_id is None:
            return "Unknown"

        try:
            team_id_int = int(team_id)
        except (TypeError, ValueError):
            return str(team_id)

        if team_id_int == 0:
            return "Unassigned"

        team_names = WVW_TEAM_NAMES.get(team_id_int)
        team_name = None
        if isinstance(team_names, dict):
            raw_name = team_names.get("en")
            if isinstance(raw_name, str):
                team_name = raw_name.strip()

        if team_name:
            return team_name

        return str(team_id_int)

    @staticmethod
    def _resolve_guild_names(api_key, account_details, api_client):
        def _clean_names(names):
            return [name.strip() for name in names if isinstance(name, str) and name.strip()]

        cached_without_tags = []

        stored_names = getattr(api_key, "guild_names", None)
        if isinstance(stored_names, list):
            cleaned_names = _clean_names(stored_names)
            if cleaned_names and all("[" in name and "]" in name for name in cleaned_names):
                return cleaned_names
            cached_without_tags = cleaned_names
        elif isinstance(stored_names, str) and stored_names.strip():
            cleaned_name = stored_names.strip()
            if "[" in cleaned_name and "]" in cleaned_name:
                return [cleaned_name]
            cached_without_tags = [cleaned_name]

        guild_ids = []
        if isinstance(account_details, dict):
            guild_ids = account_details.get("guilds") or []
            if not isinstance(guild_ids, list):
                guild_ids = []

        resolved_names = []
        for guild_id in guild_ids:
            try:
                guild_details = api_client.guild(gw2_guild_id=guild_id)
            except Exception:
                continue

            if not isinstance(guild_details, dict):
                continue

            guild_name = guild_details.get("name")
            guild_tag = guild_details.get("tag")

            if isinstance(guild_name, str) and isinstance(guild_tag, str):
                resolved_names.append(f"{guild_name} [{guild_tag}]")
            elif isinstance(guild_name, str):
                resolved_names.append(guild_name)

        if resolved_names:
            try:
                api_key.guild_names = resolved_names
                api_key.save()
            except Exception:
                pass
            return resolved_names

        if cached_without_tags:
            return cached_without_tags

        return resolved_names

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

            if len(db_member.api_keys) > 0:
                lookup_embed = discord.Embed(
                    title=f"{member.display_name} | {member.name}",
                    description="",
                )
                lookup_embed.set_thumbnail(url=member.display_avatar.url)

                api_key_count = len(db_member.api_keys)

                for index, api_key in enumerate(db_member.api_keys):
                    api_client = GW2ApiClient(api_key=api_key.value)
                    try:
                        account_details = api_client.account()
                    except Exception:
                        account_details = None

                    if isinstance(account_details, dict):
                        wvw_info = account_details.get("wvw")
                        if isinstance(wvw_info, dict):
                            wvw_rank = wvw_info.get("rank")
                            team_id = wvw_info.get("team_id")
                        else:
                            wvw_rank = None
                            team_id = None
                    else:
                        wvw_rank = None
                        team_id = None

                    wvw_rank_value = str(wvw_rank) if wvw_rank is not None else "Unknown"
                    wvw_team_value = self._format_wvw_team_name(team_id)

                    guild_names = self._resolve_guild_names(api_key, account_details, api_client)
                    if guild_names:
                        guild_lines = "\n".join(f"  - {name}" for name in guild_names)
                    elif account_details is None:
                        guild_lines = "Unknown"
                    else:
                        guild_lines = "None"

                    account_name = None
                    if isinstance(account_details, dict):
                        raw_name = account_details.get("name")
                        if isinstance(raw_name, str) and raw_name.strip():
                            account_name = raw_name.strip()

                    if not account_name:
                        fallback_name = api_key.name if isinstance(api_key.name, str) else None
                        account_name = fallback_name or "Unknown"

                    lookup_embed.add_field(
                        name="username",
                        value=f"```\n{account_name}\n```",
                        inline=False,
                    )
                    lookup_embed.add_field(
                        name="WvW Rank",
                        value=f"```\n{wvw_rank_value}\n```",
                        inline=True,
                    )
                    lookup_embed.add_field(
                        name="WvW Team",
                        value=f"```\n{wvw_team_value}\n```",
                        inline=True,
                    )
                    lookup_embed.add_field(
                        name="Guilds",
                        value=f"```\n{guild_lines}\n```",
                        inline=False,
                    )

                    if index < api_key_count - 1:
                        lookup_embed.add_field(
                            name="────────────────",
                            value="\u200b",
                            inline=False,
                        )
            else:
                no_keys_embed = discord.Embed(
                    title=f"{member.display_name} | {member.name}",
                    description="",
                )
                no_keys_embed.set_thumbnail(url=member.display_avatar.url)
                no_keys_embed.add_field(name="API Keys", value="```No API Keys found```", inline=False)
                await interaction.followup.send(embed=no_keys_embed, ephemeral=True)
                return

            await interaction.followup.send(embed=lookup_embed, ephemeral=True)


async def setup(bot):
    for guild in bot.guilds:
        await bot.add_cog(AdminLookup(bot), guild=guild, override=True)
