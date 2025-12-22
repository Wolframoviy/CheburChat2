# def login_required(f):
#     def wrap(*args, **kwargs):
#
#     return wrap
from flask import redirect, url_for, session
from app.database.UserModel import User


def key_required(f):
    def wrapper(*args, **kwargs):
        if User.get(id=session.get("user_id")).vault is None:
            return redirect(url_for("generate"))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def login_required(f):
    def wrapper(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper