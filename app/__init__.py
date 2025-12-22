from flask import Flask
from flask_socketio import SocketIO
from flask_session import Session
import os, config

app = Flask(__name__)
app.config.from_object(config.DevelopmentConfig)
Session(app)
sio = SocketIO(app, manage_session=False)

from app.database import *
from app.core import views
from app.core import socket
