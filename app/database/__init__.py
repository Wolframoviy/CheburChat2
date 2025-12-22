from app import app
from peewee import *

if app.config.get('DATABASE') == "sqlite":
    db = SqliteDatabase(app.config.get("SQLITE_PATH"), pragmas={'journal_mode': 'wal'})
elif app.config.get('DATABASE') == "postgresql":
    db = PostgresqlDatabase(
        app.config.get("DATABASE_NAME"),
        user=app.config.get("DATABASE_USER"),
        password=app.config.get("DATABASE_PASSWORD"),
        host=app.config.get("DATABASE_HOST"),
        port=app.config.get("DATABASE_PORT")
    )
else:
    raise ValueError("Unknown database type")