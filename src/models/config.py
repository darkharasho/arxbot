import pdb
import discord

from peewee import *
from playhouse.sqlite_ext import *
from config import settings
from src.models.base_model import BaseModel
from src.models.guild import Guild


class Config(BaseModel):
    name = CharField(unique=True)
    guild_id = ForeignKeyField(Guild, backref="configs")
    value = JSONField()
    value_type = TextField()

    @classmethod
    def allowed_admin_role_ids(cls):
        value = cls.select().where(cls.name == "allowed_admin_role_ids").first()
        if value:
            return value.get_value()
        else:
            return []

    @classmethod
    def create_or_update(cls, name=str, value=None, guild=discord.Guild):
        config = cls.select().where((cls.name == name) & (cls.guild_id == guild.id)).first()
        value_type = type(value).__name__
        try:
            if config:
                (Config.update(value=value, value_type=value_type)
                 .where(Config.id == config.id)
                 .execute())
                action = "update"
                config = cls.select().where(cls.id == config.id).first()
            else:
                action = "create"

                config = cls.create(name=name,
                                    value=value,
                                    value_type=value_type,
                                    guild_id=guild.id)
            return config, action
        except Exception as e:
            print(f"[ERR] {e}")
            return False, "Failed"

    # Ensure that we are correctly casting the value
    def get_value(self):
        if self.value_type == "str":
            return str(self.value)
        elif self.value_type == "int":
            return int(self.value)
        else:
            return self.value
