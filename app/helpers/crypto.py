from hashlib import sha3_512
from random import randint

def get_hash(data, salt=None):
    if salt is None:
        return sha3_512(data.encode()).hexdigest()
    return sha3_512(data.encode() + salt.encode()).hexdigest()

def check_hash(inhash, data, salt=None):
    return get_hash(data, salt) == inhash

def generate_salt():
    salt = str(randint(0, 1000))
    return get_hash(salt)