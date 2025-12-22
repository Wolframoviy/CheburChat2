import os

app_dir = os.path.abspath(os.path.dirname(__file__))

class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY")


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    DATABASE = "sqlite"
    SQLITE_PATH = ".venv/database.sqlite"
    TEMPLATES_AUTO_RELOAD = True
    SESSION_TYPE = "filesystem"


class ProductionConfig(BaseConfig):
    DEBUG = False
    DATABASE = "postgresql"
    DATABASE_NAME = "cheburchat_db"
    DATABASE_HOST = os.environ.get("DATABASE_HOST")
    DATABASE_PORT = "5432"
    DATABASE_USER = os.environ.get("DATABASE_USER")
    DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD")
    # todo: prod config