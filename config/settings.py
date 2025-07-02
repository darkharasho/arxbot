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
GW2_GUILD_ID = config['GW2GuildID']

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
        "text": "# Guild Verification:\n Create the mapping of guild -> discord role.\nFormat: `Guild Name | Guild Tag | Discord Role Name, Second Guild Name | Second Guild Tag | Second Discord Role Name, etc`",
        "field_type": "input",
        "response_type": "comma_separated_list"
    }
]

SET_CLEAN_CHANNEL = [
    {
        "text": "# Clean Channel:\nDeletes messages older than 1 week in a set channel. Helpful for bot channels like dps logs or updates.",
        "field_type": "input",
        "response_type": "text_channel"
    },
    {
        "text": "# Enabled?",
        "field_type": "select",
        "options": [True, False],
        "response_type": bool
    }
]

SERVER_NAMES = [
    {"id": 1001, "name": "Anvil Rock", "abbreviation": "AR"},
    {"id": 1002, "name": "Borlis Pass", "abbreviation": "BP"},
    {"id": 1003, "name": "Yak's Bend", "abbreviation": "YB"},
    {"id": 1004, "name": "Henge of Denravi", "abbreviation": "HoD"},
    {"id": 1005, "name": "Maguuma", "abbreviation": "Mag"},
    {"id": 1006, "name": "Sorrow's Furnace", "abbreviation": "SF"},
    {"id": 1007, "name": "Gate of Madness", "abbreviation": "GoM"},
    {"id": 1008, "name": "Jade Quarry", "abbreviation": "JQ"},
    {"id": 1009, "name": "Fort Aspenwood", "abbreviation": "FA"},
    {"id": 1010, "name": "Ehmry Bay", "abbreviation": "EB"},
    {"id": 1011, "name": "Stormbluff Isle", "abbreviation": "SBI"},
    {"id": 1012, "name": "Darkhaven", "abbreviation": "DH"},
    {"id": 1013, "name": "Sanctum of Rall", "abbreviation": "SoR"},
    {"id": 1014, "name": "Crystal Desert", "abbreviation": "CD"},
    {"id": 1015, "name": "Isle of Janthir", "abbreviation": "IoJ"},
    {"id": 1016, "name": "Sea of Sorrows", "abbreviation": "SoS"},
    {"id": 1017, "name": "Tarnished Coast", "abbreviation": "TC"},
    {"id": 1018, "name": "Northern Shiverpeaks", "abbreviation": "NSP"},
    {"id": 1019, "name": "Blackgate", "abbreviation": "BG"},
    {"id": 1020, "name": "Ferguson's Crossing", "abbreviation": "FC"},
    {"id": 1021, "name": "Dragonbrand", "abbreviation": "DB"},
    {"id": 1022, "name": "Kaineng", "abbreviation": "KN"},
    {"id": 1023, "name": "Devona's Rest", "abbreviation": "DR"},
    {"id": 1024, "name": "Eredon Terrace", "abbreviation": "ET"},
    {"id": 2001, "name": "Fissure of Woe", "abbreviation": "FoW"},
    {"id": 2002, "name": "Desolation", "abbreviation": "Des"},
    {"id": 2003, "name": "Gandara", "abbreviation": "Gan"},
    {"id": 2004, "name": "Blacktide", "abbreviation": "BT"},
    {"id": 2005, "name": "Ring of Fire", "abbreviation": "RoF"},
    {"id": 2006, "name": "Underworld", "abbreviation": "Und"},
    {"id": 2007, "name": "Far Shiverpeaks", "abbreviation": "FS"},
    {"id": 2008, "name": "Whiteside Ridge", "abbreviation": "WR"},
    {"id": 2009, "name": "Ruins of Surmia", "abbreviation": "RoS"},
    {"id": 2010, "name": "Seafarer's Rest", "abbreviation": "SR"},
    {"id": 2011, "name": "Vabbi", "abbreviation": "Vab"},
    {"id": 2012, "name": "Piken Square", "abbreviation": "PS"},
    {"id": 2013, "name": "Aurora Glade", "abbreviation": "AG"},
    {"id": 2014, "name": "Gunnar's Hold", "abbreviation": "GH"},
    {"id": 2101, "name": "Jade Sea [FR]", "abbreviation": "JS"},
    {"id": 2102, "name": "Fort Ranik [FR]", "abbreviation": "FR"},
    {"id": 2103, "name": "Augury Rock [FR]", "abbreviation": "AG"},
    {"id": 2104, "name": "Vizunah Square [FR]", "abbreviation": "VS"},
    {"id": 2105, "name": "Arborstone [FR]", "abbreviation": "Arb"},
    {"id": 2201, "name": "Kodash [DE]", "abbreviation": "Kod"},
    {"id": 2202, "name": "Riverside [DE]", "abbreviation": "RS"},
    {"id": 2203, "name": "Elona Reach [DE]", "abbreviation": "ER"},
    {"id": 2204, "name": "Abaddon's Mouth [DE]", "abbreviation": "AM"},
    {"id": 2205, "name": "Drakkar Lake [DE]", "abbreviation": "DL"},
    {"id": 2206, "name": "Miller's Sound [DE]", "abbreviation": "MS"},
    {"id": 2207, "name": "Dzagonur [DE]", "abbreviation": "Dzg"},
    {"id": 2301, "name": "Baruch Bay [SP]", "abbreviation": "BB"}
]
