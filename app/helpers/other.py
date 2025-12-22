from app.database.UserModel import User

def message_payload(message):
    user = User.get(id=message.author)
    dn = user.display_name
    if dn is None or dn == "":
        dn = user.username
    payload = {
        "author": dn,
        "data": message.data,
        "timestamp": message.timestamp,
        "iv": message.iv
    }
    return payload