from flask import render_template, redirect, request, url_for, session, flash, abort, Response
from time import time
from datetime import datetime

from app import app
from app.database.ChatModel import Chat
from app.database.UserModel import User
from app.database.MessageModel import Message
from app.helpers.crypto import generate_salt, get_hash, check_hash
from app.helpers.decorators import *

@app.route('/', methods=['GET'])
def index():
    return render_template("index.html")

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html")

    if not request.form.get("username", False):
        flash("Укажите имя пользователя!")
        return redirect(url_for("login"))

    if not request.form.get("password", False):
        flash("Укажите пароль!")
        return redirect(url_for("login"))

    user = User.get_or_none(username=request.form.get("username"))
    if user is None:
        flash("Пользователь не найден!")
        return redirect(url_for("login"))

    if not check_hash(user.password, request.form.get("password"), user.salt):
        flash("Неверные данные!")
        return redirect(url_for("login"))

    session["user_id"] = user.id

    return redirect(url_for("restore_key"))

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template("register.html")

    if not request.form.get("username", False):
        flash("Укажите имя пользователя!")
        return redirect(url_for("register"))

    if not request.form.get("password", False):
        flash("Укажите пароль!")
        return redirect(url_for("register"))

    if request.form.get("password") != request.form.get("repassword", None):
        flash("Пароли не сопадают!")
        return redirect(url_for("register"))

    if User.get_or_none(username=request.form.get("username")):
        flash("Имя пользователя используется!")
        return redirect(url_for("register"))

    salt = generate_salt()

    user = User.create(
        username=request.form.get("username"),
        password= get_hash(request.form.get("password"), salt),
        salt=salt,
        registered_on=time()
    )

    user.save()

    session["user_id"] = user.id

    return redirect(url_for("generate"))

@app.route('/generate/', methods=['GET', 'POST'])
def generate():
    if request.method == 'GET':
        if session.get("key_generated", 0):
            return redirect(url_for("profile"))

        return render_template("generate.html")

    publickey = request.json.get("publicKey", None)
    privatekey = request.json.get("privateKey", None)
    salt = request.json.get("salt", None)
    iv = request.json.get("iv", None)

    if not (publickey and privatekey and salt and iv):
        return redirect(url_for("generate"))

    user = User.select().where(User.id == session.get("user_id")).first()
    user.vault = privatekey
    user.public = publickey
    user.salt2 = salt
    user.iv = iv
    user.save()

    return redirect(url_for("me"))

@app.route("/restore_key/")
@login_required
def restore_key():
    return render_template("get_keys.html")

@app.route("/logout/")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/me/")
@login_required
def me():
    user = User.get(id=session.get("user_id"))
    return render_template("my_profile.html", user=user, datetime=datetime)

@app.route("/user/<string:username>")
def user(username):
    user = User.get(username=username)
    return render_template("profile.html", user=user, datetime=datetime)

@app.route("/user/")
def users():
    return render_template("userslist.html", users=User.select())

@app.route("/chats/<int:chat_id>/")
@key_required
@login_required
def chats(chat_id):
    chat = Chat.get_or_none(id=chat_id)
    if chat is None:
        return abort(404)
    if not (chat.first_member_id == session.get("user_id") or chat.second_member_id == session.get("user_id")):
        return abort(403)

    if chat.first_member_id == session.get("user_id"):
        companion = User.get(id=chat.second_member_id)
    else:
        companion = User.get(id=chat.first_member_id)

    chatlist = Chat.select().where((Chat.first_member_id == session.get("user_id")) | (Chat.second_member_id == session.get("user_id"))).order_by(Chat.last_message_time.desc())

    return render_template("messanger.html", chat=chat, companion=companion, chatlist=chatlist, User=User)

@app.route("/chats/")
@key_required
@login_required
def chats_list():
    chatlist = Chat.select().where(
        (Chat.first_member_id == session.get("user_id")) | (Chat.second_member_id == session.get("user_id"))).order_by(
        Chat.last_message_time.desc())
    return render_template("messanger_none.html", chatlist=chatlist, User=User)

@app.route("/start/", methods=["GET", "POST"])
@key_required
@login_required
def start_chat():
    if request.method == "GET":
        first_id = session.get("user_id")
        second_id = request.args.get("with")

        user1 = User.get_or_none(id=first_id)
        user2 = User.get_or_none(id=second_id)

        if user2 is None:
            abort(404)
        if user1.id == user2.id:
            return redirect(url_for("me"))

        return render_template("start_chat.html", user=user2)

    first_id = session.get("user_id")
    second_id = request.json.get("user2_id")

    user1 = User.get_or_none(id=first_id)
    user2 = User.get_or_none(id=second_id)

    if user2 is None:
        return abort(404)
    if user1.id == user2.id:
        return abort(403)

    if Chat.get_or_none((Chat.first_member_id==user1.id and Chat.second_member_id==user2.id) or (Chat.first_member_id == user2.id and Chat.second_member_id == user1.id)):
        return abort(418)

    chat = Chat.create(
        first_member_id=user1.id,
        second_member_id=user2.id,
        first_member_key=request.json.get("user1aes"),
        second_member_key=request.json.get("user2aes"),
    )

    chat.save()

    return Response(status=200)


@app.route("/api/user/key/", methods=["POST"])
@login_required
def user_key():
    user = User.get(id=session.get("user_id"))
    payload = {
        "privateKey": user.vault,
        "publicKey": user.public,
        "salt": user.salt2,
        "iv": user.iv,
    }

    return payload

@app.route("/api/user/public/<int:user_id>", methods=["GET"])
def user_public(user_id):
    user = User.get_or_none(id=user_id)
    if user is None:
        return abort(404)

    return {"publicKey": user.public}

@app.route("/api/chats/aes/<int:chat_id>")
@login_required
def get_chat_key(chat_id):
    chat = Chat.get_or_none(id=chat_id)

    if chat is None:
        return abort(404)
    if not ((chat.first_member_id == session.get("user_id")) or (chat.second_member_id == session.get("user_id"))):
        return abort(418)

    if chat.first_member_id == session.get("user_id"):
        return {"aes": chat.first_member_key}
    else:
        return {"aes": chat.second_member_key}


