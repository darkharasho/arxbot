import pdb

import discord
from config import settings
from src import helpers
from src.models.config import Config


async def ensure_admin(interaction):
    user_role_ids = [role.id for role in interaction.user.roles]
    allowed_admin_role_ids = Config.allowed_admin_role_ids(guild_id=interaction.guild.id)

    if not allowed_admin_role_ids:
        for role in interaction.user.roles:
            if role.permissions.administrator:
                return True
        if interaction.user.guild_permissions.administrator:
            return True

    if not any(role_id in allowed_admin_role_ids for role_id in user_role_ids):
        embed = discord.Embed(title="Unauthorized", description="You do not have permission to run this command.",
                              color=0xff0000)

        file_name = helpers.select_icon("unauthorized")
        file = discord.File(file_name)
        embed.set_thumbnail(url=f"attachment://{file.filename}")
        await interaction.response.send_message(
            embed=embed, file=file, ephemeral=True)
        return False
    return True

def ensure_creator(ctx):
    if ctx.author.id == 201537071804973056:
        return True
    else:
        return False
