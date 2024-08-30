import discord
from discord.ext import commands
from discord import app_commands
from src import authorization
from src.models.member import Member


class AdminGuildLookup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="admin_guild_lookup",
        description="Admin: Display members of a role and their GW2 account names if available"
    )
    async def admin_guild_lookup(self, interaction: discord.Interaction, role: discord.Role):
        if await authorization.ensure_admin(interaction):
            await interaction.response.defer(ephemeral=True)

            # Get all members with the specified role
            members_with_role = [member for member in interaction.guild.members if role in member.roles]

            if not members_with_role:
                await interaction.followup.send(f"No members found with the role {role.name}.", ephemeral=True)
                return

            embed = discord.Embed(
                title=f"Members with Role: {role.name}",
                description=f"Listing members with the role {role.name} and their GW2 account names if available."
            )

            for member in members_with_role:
                db_member = Member.find_or_create(member=member, guild=interaction.guild)
                gw2_accounts = [api_key.name for api_key in db_member.api_keys] if db_member.api_keys else [
                    "No API Key"]
                gw2_accounts_str = "\n- ".join(gw2_accounts)

                embed.add_field(
                    name=f"{member.display_name} ({member.name})",
                    value=f"GW2 Accounts: ```- {gw2_accounts_str}```",
                    inline=False
                )

            await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    for guild in bot.guilds:
        await bot.add_cog(AdminGuildLookup(bot), guild=guild, override=True)
