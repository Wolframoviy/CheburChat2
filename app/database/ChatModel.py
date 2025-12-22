from peewee import *
from . import db

class Chat(Model):
    id = IntegerField(primary_key=True)
    first_member_id = IntegerField()
    second_member_id = IntegerField()
    first_member_key = CharField()
    second_member_key = CharField()
    last_message_time = DateTimeField(default=0)

    class Meta:
        database = db
        table_name = 'chats'

if not db.table_exists('chats'):
    db.create_tables([Chat], safe=True)