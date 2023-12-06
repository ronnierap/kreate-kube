from cryptography.fernet import Fernet
import logging
import os
import sys

logger = logging.getLogger(__name__)

_key_finder = None
_krypt_key = None
_dekrypt_testdummy = False


def _get_key():
    global _krypt_key
    if not _krypt_key:
        global _key_finder
        if not _key_finder:
            raise ValueError("No konfig tosearch for _krypt_key")
        _krypt_key = _key_finder.get_krypt_key()
        if not _krypt_key:
            raise ValueError("_krypt_key is empty")
    return Fernet(_krypt_key)


def dekrypt_str(value: str) -> str:
    return dekrypt_bytes(value).decode()


def dekrypt_bytes(value: bytes) -> bytes:
    fernet = _get_key()
    if _dekrypt_testdummy:
        format = os.getenv("KREATE_DUMMY_DEKRYPT_FORMAT")
        format = format or "test-dummy"
        return format.format(value=value).encode()
    return fernet.decrypt(value)


def dekrypt_file(filename: str):
    fernet = _get_key()
    with open(filename) as f:
        data = f.read()
    if _dekrypt_testdummy:
        format = os.getenv("KREATE_DUMMY_DEKRYPT_FORMAT")
        format = format or "testdummy-{value[len(value)//2-4:len(value)//2+4]}"
        return format.format(value=data)
    with open(filename + ".decrypted", "wb") as out:
        out.write(fernet.decrypt(data.encode()))


def enkrypt_str(value):
    fernet = _get_key()
    part = b"\xbd\xc0,\x16\x87\xd7G\xb5\xe5\xcc\xdb\xf9\x07\xaf\xa0\xfa"
    # use the parts to prevent changes if secret was not changed
    return fernet._encrypt_from_parts(value.encode(), 0, part).decode()


def enkrypt_file(filename: str):
    fernet = _get_key()
    with open(filename, "rb") as f:
        data = f.read()
    with open(filename + ".encrypted", "wb") as f:
        part = b"\xbd\xc0,\x16\x87\xd7G\xb5\xe5\xcc\xdb\xf9\x07\xaf\xa0\xfa"
        f.write(fernet._encrypt_from_parts(data, 0, part))


def change_lines(
    filename: str, func, from_: str, to_: str, dir: str = None, stdout=False
):
    dir = dir or "."
    with open(f"{dir}/{filename}") as f:
        lines = f.readlines()
    for idx, line in enumerate(lines):
        # line = line.rstrip()
        if from_ in line:
            try:
                parts = line.split(from_, 1)
                value = parts[1].strip()
                start = parts[0]
                logger.info(f"{from_} {parts[0].strip()} ...")
                value = func(value)
                lines[idx] = f"{start}{to_}{value}\n"
            except Exception as e:
                logger.error(f"problem with {func} in {parts[0]}: {e}")
    if stdout:
        sys.stdout.writelines(lines)
    else:
        with open(f"{dir}/{filename}", "w") as f:
            f.writelines(lines)


def dekrypt_lines(filename: str, dir: str = None, stdout=False):
    change_lines(filename, dekrypt_str, "dekrypt:", "enkrypt:", dir=dir, stdout=stdout)


def enkrypt_lines(filename: str, dir: str = None, stdout=False):
    change_lines(filename, enkrypt_str, "enkrypt:", "dekrypt:", dir=dir, stdout=stdout)
