from cryptography.fernet import Fernet
import logging

logger = logging.getLogger(__name__)


_krypt_key = None
_dekrypt_testdummy = False


def _get_key():
    if not _krypt_key:
        raise ValueError("_krypt_key is empty")
    return Fernet(_krypt_key)


def dekrypt_str(value):
    fernet = _get_key()
    if _dekrypt_testdummy:
        return f"testdummy-{value[len(value)//2-4:len(value)//2+4]}"
    return fernet.decrypt(value.encode("ascii")).decode("ascii")


def dekrypt_bytes(value: bytes) -> bytes:
    fernet = _get_key()
    if _dekrypt_testdummy:
        return f"testdummy-{value[len(value)//2-4:len(value)//2+4]}"
    return fernet.decrypt(value)


def dekrypt_file(filename):
    fernet = _get_key()
    with open(filename) as f:
        data = f.read()
    if _dekrypt_testdummy:
        data = f"testdummy-{data[len(data)//2-4:len(data)//2+4]}"
    print(fernet.decrypt(data.encode("ascii")).decode("ascii"), end="")


def enkrypt_str(value):
    fernet = _get_key()
    part = b"\xbd\xc0,\x16\x87\xd7G\xb5\xe5\xcc\xdb\xf9\x07\xaf\xa0\xfa"
    # use the parts to prevent changes if secret was not changed
    return fernet._encrypt_from_parts(value.encode("ascii"), 0, part).decode(
        "ascii"
    )


def enkrypt_file(filename):
    fernet = _get_key()
    with open(filename) as f:
        data = f.read()
    with open(filename + ".encrypted", "wb") as f:
        part = b"\xbd\xc0,\x16\x87\xd7G\xb5\xe5\xcc\xdb\xf9\x07\xaf\xa0\xfa"
        f.write(fernet._encrypt_from_parts(data.encode("ascii"), 0, part))


def change_lines(filename: str, func, from_: str, to_: str, dir: str = None):
    dir = dir or "."
    with open(f"{dir}/{filename}") as f:
        lines = f.readlines()
    for idx, line in enumerate(lines):
        line = line.rstrip()
        if line.endswith(from_):
            line = line[: -len(from_)]
            value = line.rsplit(":", 1)[1].strip()
            start = line.rsplit(":", 1)[0]
            value = func(value)
            lines[idx] = f"{start}: {value}  {to_}\n"
    with open(f"{dir}/{filename}", "w") as f:
        f.writelines(lines)


def dekrypt_lines(filename: str, dir: str = None):
    change_lines(filename, dekrypt_str, "# enkrypted", "# dekrypted", dir=dir)


def enkrypt_lines(filename: str, dir: str = None):
    change_lines(filename, enkrypt_str, "# dekrypted", "# enkrypted", dir=dir)
