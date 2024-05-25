# settings.py
import json
import discord

# Configuration variables
raw_config = open('config/config.json')
config = json.load(raw_config)

# Mandatory
TOKEN = config['Token']
APPLICATION_ID = config['ApplicationID']
