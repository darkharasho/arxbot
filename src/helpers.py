##################################
# Helpers ########################
##################################
import discord
import re
import os
from discord.ext import commands
from config import settings

def command_to_cog(command):
    cmd2cog = re.sub(r'-', '_', command)
    cmd2cog = re.sub(r'_cog', '', cmd2cog)
    cmd2cog = re.sub(r'_', '', (cmd2cog + "_cog").title())
    return cmd2cog

def select_icon(icon_name, file_type="png"):
    img_dir = os.path.dirname(os.path.abspath(__file__))

    if icon_name:
        selected_file = os.path.join(img_dir, f"../icons/{icon_name}.{file_type}")
    else:
        selected_file = None

    return selected_file

def get_by_name(nameable_objects, name):
    for nameable_object in nameable_objects:
        if nameable_object.name == name:
            return nameable_object
    return None


def get_by_list_of_names(nameable_objects, names):
    objects = []
    for name in names:
        obj = get_by_name(nameable_objects, name)
        if obj:
            objects.append(obj)
    return objects

def align_list(list_to_align):
    result_array = []

    # Iterate through each sub-array and join its elements with proper spacing
    for sub_array in list_to_align:
        # Join the elements with a space and add the result to the result array
        result = " ".join(sub_array)
        result_array.append(result)

    return "\n".join(result_array)


def strip_emojis(text):
    # Define a regular expression pattern to match emojis
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # Emoticons
                               u"\U0001F300-\U0001F5FF"  # Miscellaneous Symbols and Pictographs
                               u"\U0001F680-\U0001F6FF"  # Transport and Map Symbols
                               u"\U0001F700-\U0001F77F"  # Alchemical Symbols
                               u"\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
                               u"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
                               u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
                               u"\U0001FA00-\U0001FA6F"  # Chess Symbols
                               u"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
                               u"\U0001F004-\U0001F0CF"  # Additional emoticons
                               u"\U0001F200-\U0001F251"  # Additional T-shaped images
                               "]+", flags=re.UNICODE)

    # Use re.sub to remove emojis
    text_without_emojis = emoji_pattern.sub('', text)

    return text_without_emojis


def check_guild_role(member=discord.Member):
    return Config.guild_member_role_id() in [role.id for role in member.roles]


async def find_role_by_name(guild, role_name):
    for role in guild.roles:
        if role.name.lower() == role_name.lower():
            return role
    return None


def find_emoji_by_name_pattern(name):
    guild = bot.get_guild(settings.GUILD_ID)
    best_match, score = process.extractOne(name, [emoji.name for emoji in guild.emojis])

    if score < 30:
        return "✅"

    full_emoji = None
    for emoji in guild.emojis:
        if best_match == emoji.name:
            full_emoji = emoji

    if full_emoji:
        return f"<:{full_emoji.name}:{full_emoji.id}>"
    else:
        return "✅"

def format_number(number):
    number = int(number)
    if number < 1000:
        return str(number)
    elif number < 10000:
        return f"{number // 1000}k"
    elif number < 1000000:
        return f"{number / 1000:.1f}k"
    elif number < 10000000:
        return f"{number // 1000000}M"
    else:
        return f"{number / 1000000:.1f}M"


def abbreviate_world_name(server_name):
    for listed_server in settings.SERVER_NAMES:
        if listed_server["name"] == server_name:
            return listed_server["abbreviation"]
    return "N/A"


def calculate_kd(kills: int, deaths: int):
    if kills == 0:
        return 0
    elif deaths == 0:
        return kills
    kd_float = kills / deaths
    return float("%.2f" % kd_float)
