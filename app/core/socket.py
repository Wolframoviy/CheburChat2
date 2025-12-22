from flask import session, request
from flask_socketio import join_room, leave_room
from time import time

from app import sio
from app.database.UserModel import User
from app.database.ChatModel import Chat
from app.database.MessageModel import Message
from app.helpers.other import message_payload


@sio.on("status.update")
def connect(data):
    chat = Chat.get_or_none(id=data.get("chat_id"))
    user = User.get_or_none(id=session.get("user_id"))
    if chat is None:
        sio.emit("error", {"message": "Chat not found"}, to=request.sid)
        return

    if not (chat.first_member_id == user.id or chat.second_member_id == user.id):
        sio.emit("error", {"message": "You are not the chat member"}, to=request.sid)
        return

    user.status = chat.id
    user.save()

    join_room(chat.id)

    print(f"{session.get('user_id')} connected to {data.get('chat_id')}")

@sio.on("disconnect")
def disconnect():
    user = User.get_or_none(id=session.get("user_id"))
    leave_room(user.status)
    user.status = 0
    user.save()

@sio.on("message.send")
def send(data):
    chat = Chat.get_or_none(id=data.get("chat_id"))
    user = User.get_or_none(id=session.get("user_id"))
    if chat is None:
        sio.emit("error", {"message": "Chat not found"}, to=request.sid)
        return

    if not (chat.first_member_id == user.id or chat.second_member_id == user.id):
        sio.emit("error", {"message": "You are not the chat member"}, to=request.sid)
        return

    message = Message.create(
        data=data.get("data"),
        author=user.id,
        chat=chat.id,
        timestamp=time(),
        iv=data.get("iv"),
    )
    message.save()
    chat.last_message_time = time()
    chat.save()

    sio.emit("message.ack", to=request.sid)
    sio.emit("message.new", message_payload(message), to=chat.id)

@sio.on("message.loadHistory")
def loadHistory(data):
    chat = Chat.get_or_none(id=data.get("chat_id"))
    user = User.get_or_none(id=session.get("user_id"))
    if chat is None:
        sio.emit("error", {"message": "Chat not found"}, to=request.sid)
        return

    if not (chat.first_member_id == user.id or chat.second_member_id == user.id):
        sio.emit("error", {"message": "You are not the chat member"}, to=request.sid)
        return
    if data.get("from") != -1:
        messages = Message.select().where(Message.chat == chat.id and Message.id < data.get("from")).order_by(Message.timestamp.desc()).limit(25)
    else:
        messages = Message.select().where(Message.chat == chat.id).order_by(Message.timestamp.desc()).limit(25)

    messages_payload = list(map(message_payload, messages))

    sio.emit("message.history", {"end": len(messages_payload) < 25, "messages": messages_payload, "last": messages[-1].id}, to=request.sid)
