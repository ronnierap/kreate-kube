from cryptography.fernet import Fernet
from ruamel.yaml import YAML
import logging

logger = logging.getLogger(__name__)



_krypt_key = None

def dekrypt_str(value):
    f = Fernet(_krypt_key)
    return f.decrypt(value.encode("ascii")).decode("ascii")

def enkrypt_str(value):
    f = Fernet(_krypt_key)
    return f.encrypt(value.encode("ascii")).decode("ascii")



def change_yaml_comments( filename: str, func, from_: str, to_ :str, dir: str = None):
    dir = dir or "."
    yaml_parser = YAML()
    with open(f"{dir}/{filename}") as f:
        data = f.read()
    yaml = yaml_parser.load(data)
    ca = yaml['secrets'].ca
    for key in yaml.get("secrets", {}):
        if key in ca.items: # and len(ca.items[key])>2:
            item = yaml["secrets"][key]
            comment=ca.items[key][2]
            if from_ in comment.value:
                comment.column = 0
                comment.value = "   "+comment.value.replace(from_, to_,1)
                yaml["secrets"][key] = func(item)
                logger.info(f"{to_} {key}")

    with open(f"{dir}/{filename}", 'wb') as f:
        yaml_parser.dump(yaml, f)

def dekrypt_yaml( filename: str, dir: str = None):
    change_yaml_comments(filename, dekrypt_str, "enkrypted", "dekrypted", dir=dir)

def enkrypt_yaml( filename: str, dir: str = None):
    change_yaml_comments(filename, enkrypt_str, "dekrypted", "enkrypted", dir=dir)
