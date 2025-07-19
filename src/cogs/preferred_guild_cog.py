import discord
from discord.ext import commands
from discord import app_commands


class PreferredGuildCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.allowed_roles = {"DUI", "EWW", "PUGS", "UA", "FAFO", "PYRO", "Goon"}

    @app_commands.command(
        name="preferred-guild",
        description="Set your preferred guild role."
    )
    async def preferred_guild(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        try:
            # Filter the user's roles to only include the allowed ones
            roles = [
                role for role in interaction.user.roles
                if role.name in self.allowed_roles and role != interaction.guild.default_role
            ]
            roles.sort(key=lambda r: r.position, reverse=True)

            if not roles:
                await interaction.followup.send("You don't have any roles that can be set as a preferred guild role.",
                                                ephemeral=True)
                return

            # Create a select menu for roles
            options = [
                discord.SelectOption(label=role.name, value=str(role.id))
                for role in roles
            ]

            select = discord.ui.Select(
                placeholder="Choose your preferred role...",
                options=options
            )

            async def select_callback(interaction: discord.Interaction):
                selected_role_id = int(select.values[0])
                selected_role = interaction.guild.get_role(selected_role_id)

                # Remove roles higher than the selected one, but only those in the allowed_roles list
                roles_to_remove = [
                    role for role in interaction.user.roles
                    if role.position > selected_role.position and role.name in self.allowed_roles
                ]
                try:
                    await interaction.user.remove_roles(*roles_to_remove)

                    # Confirm the action
                    embed = discord.Embed(
                        title="Preferred Role Set",
                        description=f"Roles higher than **{selected_role.name}** have been removed."
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                except discord.Forbidden:
                    await interaction.response.send_message(
                        "I don't have permission to remove some roles. Please check my permissions and role hierarchy.",
                        ephemeral=True
                    )

            select.callback = select_callback

            # Create a view and add the select menu
            view = discord.ui.View()
            view.add_item(select)

            embed = discord.Embed(
                title="Set Preferred Role",
                description="Please select your preferred guild role."
            )
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)


async def setup(bot):
    for guild in bot.guilds:
        await bot.add_cog(PreferredGuildCog(bot), guild=guild, override=True)
