# settings.py
import json
import discord

# Configuration variables
raw_config = open('config/config.json')
config = json.load(raw_config)

# Mandatory
TOKEN = config['Token']
APPLICATION_ID = config['ApplicationID']
GW2_API_KEY = config['GW2ApiKey']
MAX_LEADERBOARD_MEMBERS = config.get('MaxLeaderboardMembers', 7)

SET_USER_CHANNELS = [
    {
        "text": "# Leaderboard\n### Channels to allow users to use the /leaderboard command",
        "field_type": "input",
        "response_type": "text_channels"
    },
    {
        "text": "# Funderboard\n### Channels to allow users to use the /funderboard command",
        "field_type": "input",
        "response_type": "text_channels"
    },
    {
        "text": "# Chat\n### Channels to allow users to chat with the bot",
        "field_type": "input",
        "response_type": "text_channels"
    }
]

SET_GUILD_TO_ROLE = [
    {
        "text": "# Guild to Role Mapping:\nPlease follow the format:\nROLE_NUMBER - GUILD_NAME, (i.e. 1 Pending Alliance Name, 2 - Guild Name Two)",
        "field_type": "input",
        "response_type": "roles_custom"
    }
]

SET_VERIFICATION = [
    {
        "text": "# Guild Verification:\n What are the full, exact, guild names of the allowed guilds?",
        "field_type": "input",
        "response_type": "comma_separated_list"
    },
    {
        "text": "# Guild Verification:\n Which roles should be auto assigned based on Guild Tag?",
        "field_type": "input",
        "response_type": "roles"
    },
    {
        "text": "# Guild Verification:\n Additional roles to always add?",
        "field_type": "input",
        "response_type": "roles"
    }
]
