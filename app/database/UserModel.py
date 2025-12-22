from peewee import *
from . import db


class User(Model):
    id = IntegerField(primary_key=True)
    username = CharField(unique=True)
    email = CharField(unique=True, null=True)
    number  = IntegerField(unique=True, null=True)
    password = CharField()
    salt = CharField()
    status = IntegerField(default=0)
    registered_on = DateTimeField()
    last_login_on = DateTimeField(null=True)
    last_login_ip = CharField(null=True)
    display_name = CharField(null=True)
    birthday = DateTimeField(null=True)
    vault = CharField(null=True)
    public = CharField(null=True)
    salt2 = CharField(null=True)
    iv = CharField(null=True)

    class Meta:
        database = db
        table_name = 'users'

if not db.table_exists('users'):
    db.create_tables([User], safe=True)