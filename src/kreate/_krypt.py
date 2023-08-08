import jinja2.filters
from cryptography.fernet import Fernet

def dekrypt(value):
    # TODO: configure which key to use
    key=b'C6XOvZALFPjTzWKOPV3EJFIpmmwMhXEEqtMAG26W7_c='
    f = Fernet(key)
    return f.decrypt(value.encode("ascii")).decode("ascii")

jinja2.filters.FILTERS["dekrypt"] = dekrypt
