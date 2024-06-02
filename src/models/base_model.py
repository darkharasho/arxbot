from peewee import *
from playhouse.sqlite_ext import *

database = SqliteDatabase('arxbot.db')


class BaseModel(Model):
    class Meta:
        database = database
