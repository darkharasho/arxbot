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
MAX_LEADERBOARD_MEMBERS = config.get('MaxLeaderboardMembers', 10)

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
