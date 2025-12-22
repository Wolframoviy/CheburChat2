from peewee import *
from . import db

class Message(Model):
    id = IntegerField(primary_key=True)
    data = CharField()
    author = IntegerField()
    chat = IntegerField()
    timestamp = DateTimeField()
    iv = CharField()

    class Meta:
        database = db
        table_name = 'messages'

if not db.table_exists('messages'):
    db.create_tables([Message], safe=True)