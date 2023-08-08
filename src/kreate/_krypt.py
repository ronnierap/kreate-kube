import jinja2.filters
from cryptography.fernet import Fernet

_krypt_key = None

def dekrypt(value):
    # TODO: configure which key to use
    f = Fernet(_krypt_key)
    return f.decrypt(value.encode("ascii")).decode("ascii")

jinja2.filters.FILTERS["dekrypt"] = dekrypt
