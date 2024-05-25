import pdb

import discord
from peewee import *
from playhouse.sqlite_ext import *
from src.models.base_model import BaseModel


class Guild(BaseModel):
    name = TextField(null=False)
    guild_id = IntegerField(null=False, unique=True)
