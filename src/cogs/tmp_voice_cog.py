import discord
from discord.ext import commands
from discord import app_commands
from src.models.config import Config

class TmpVoiceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.temp_channels = {}

    @app_commands.command(name="tmp_voice",
                          description="Create a temporary voice channel with specified roles allowed to join.")
    @app_commands.describe(roles="Roles allowed to join the voice channel")
    async def tmp_voice(self, interaction: discord.Interaction, roles: str):
        guild = interaction.guild
        member = interaction.user

        # Get the role IDs from the config
        role_ids = Config.view_tmp_vc_role_ids(guild_id=interaction.guild.id)
        allowed_roles = [guild.get_role(role_id) for role_id in role_ids if guild.get_role(role_id)]

        # Parse the roles input
        role_mentions = roles.split()
        role_objects = []
        for mention in role_mentions:
            role_id = int(mention.strip('<@&>'))
            role = guild.get_role(role_id)
            if role:
                role_objects.append(role)

        if not role_objects:
            await interaction.response.send_message("No valid roles provided.", ephemeral=True)
            return

        # Create overwrites for the roles
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(connect=True, move_members=True, manage_channels=True)
        }

        for role in role_objects:
            overwrites[role] = discord.PermissionOverwrite(connect=True)

        for role in allowed_roles:
            overwrites[role] = discord.PermissionOverwrite(view_channel=True, connect=False)

        # Create a new voice channel
        temp_channel = await guild.create_voice_channel(
            name=f"Temp Voice - {', '.join(role.name for role in role_objects)}",
            overwrites=overwrites
        )

        # Store the temp channel ID
        self.temp_channels[temp_channel.id] = temp_channel

        await interaction.response.send_message(
            f"Temporary voice channel '{temp_channel.name}' created, accessible only to {', '.join(role.mention for role in role_objects)}.",
            ephemeral=True
        )

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # Check if the member left a temp voice channel
        if before.channel and before.channel.id in self.temp_channels:
            channel = before.channel
            if len(channel.members) == 0:
                await channel.delete()
                del self.temp_channels[channel.id]

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        for channel_id in list(self.temp_channels):
            channel = self.bot.get_channel(channel_id)
            if channel and channel.guild == guild:
                del self.temp_channels[channel_id]
async def setup(bot):
    for guild in bot.guilds:
        await bot.add_cog(TmpVoiceCog(bot), guild=guild, override=True)