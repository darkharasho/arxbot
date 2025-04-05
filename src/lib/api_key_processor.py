import discord
from src.gw2_api_client import GW2ApiClient
from src.models.member import Member

class ApiKeyProcessor:
    def __init__(self, bot):
        self.bot = bot

    async def process_key(self, interaction, gw2_api_key: str):
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(
            title="Checking API key...",
            description=f"```{gw2_api_key}```"
        )
        embed.add_field(name="Permissions", value="", inline=False)
        for check in ["🔃 Account", "🔃 WvW", "🔃 Progression", "🔃 Characters", "🔃 Builds", "🔃 Inventories"]:
            embed.add_field(name=check, value="")
        embed.add_field(name="", value="")

        response = await interaction.followup.send(embed=embed, ephemeral=True)
        db_member = Member.find_or_create(member=interaction.user, guild=interaction.guild)
        api_client = GW2ApiClient(api_key=gw2_api_key)
        api_checks = {}
        api_checks_display = []
        successful_permissions = []

        # Permission checks
        permissions_map = {
            "account": api_client.account,
            "wvw": api_client.wvw,
            "progression": api_client.account_achievements,
            "characters": api_client.characters,
            "builds": lambda: api_client.builds(index=0, tabs="all"),
            "inventories": api_client.bank,
        }

        for index, (permission, check_func) in enumerate(permissions_map.items(), start=1):
            try:
                if not check_func():
                    raise
                api_checks[permission] = True
                api_checks_display.append(f"✅ {permission.capitalize()}")
                successful_permissions.append(permission)
                embed.set_field_at(index=index, name=f"✅ {permission.capitalize()}", value="", inline=True)
            except:
                api_checks[permission] = False
                api_checks_display.append(f"❌ {permission.capitalize()}")
                embed.set_field_at(index=index, name=f"❌ {permission.capitalize()}", value="", inline=True)
            await response.edit(embed=embed)

        return {
            "api_checks": api_checks,
            "api_checks_display": api_checks_display,
            "successful_permissions": successful_permissions,
            "embed": embed,
            "response": response,
            "db_member": db_member,
            "api_client": api_client,
        }