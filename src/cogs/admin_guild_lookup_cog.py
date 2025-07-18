import discord
from discord.ext import commands
from discord import app_commands
from src import authorization
from src.models.member import Member

MAX_EMBED_FIELDS = 25  # Discord allows up to 25 fields per embed


class AdminGuildLookup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="admin_guild_lookup",
        description="Admin: Display members of a role and their GW2 account names if available"
    )
    async def admin_guild_lookup(self, interaction: discord.Interaction, role: discord.Role):
        if await authorization.ensure_admin(interaction):
            await interaction.response.defer(ephemeral=False)

            # Get all members with the specified role
            members_with_role = [member for member in interaction.guild.members if role in member.roles]

            if not members_with_role:
                await interaction.followup.send(f"No members found with the role {role.name}.", ephemeral=False)
                return

            # Prepare to create multiple embeds if necessary
            embeds = []
            current_embed = discord.Embed(
                title=f"Members with Role: {role.name}",
                description=f"Listing members with the role {role.name} and their GW2 account names if available."
            )
            field_count = 0

            for member in members_with_role:
                db_member = Member.find_or_create(member=member, guild=interaction.guild)
                gw2_accounts = [api_key.name for api_key in db_member.api_keys] if db_member.api_keys else [
                    "No API Key"]
                gw2_accounts_str = "\n- ".join(gw2_accounts)
                # List all roles except @everyone
                role_names = [role.name for role in member.roles if role.name != "@everyone"]
                roles_str = ", ".join(role_names) if role_names else "None"

                current_embed.add_field(
                    name=f"{member.display_name} ({member.name})",
                    value=f"GW2 Accounts: ```- {gw2_accounts_str}```\nRoles: {roles_str}",
                    inline=False
                )
                field_count += 1

                # Check if the current embed is full
                if field_count >= MAX_EMBED_FIELDS:
                    embeds.append(current_embed)
                    current_embed = discord.Embed(
                        title=f"Members with Role: {role.name}",
                        description=f"Continuing list of members with the role {role.name} and their GW2 account names."
                    )
                    field_count = 0

            # Append any remaining fields
            if field_count > 0:
                embeds.append(current_embed)

            # Send the embeds one by one
            for embed in embeds:
                await interaction.followup.send(embed=embed, ephemeral=False)


async def setup(bot):
    for guild in bot.guilds:
        await bot.add_cog(AdminGuildLookup(bot), guild=guild, override=True)
