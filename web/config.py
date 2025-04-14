from database import basedir
import os


class Config(object):
    SECRET_KEY = os.urandom(12)
    SESSION_TYPE = "filesystem"
    SESSION_PERMANENT = False
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{basedir}/database.db'