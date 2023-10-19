"""
a very simple loader of .env file as environment variables

it seemed overkill to install the dotenv package just for
this functionality
"""

import os
from pathlib import Path


def load_env(path: Path, mandatory: bool = False) -> None:
    if not path.is_file():
        if not mandatory:
            return
        raise FileNotFoundError(f"Could not find mandatory env file {path}")
    with open(path) as file:
        lines = [line.strip() for line in file]

    for line in lines:
        try:
            if line.startswith("#") or len(line) == 0:
                continue
            k, v = line.split("=", 1)
            if k not in os.environ:
                os.environ[k.strip()] = v.strip()
        except Exception as e:
            raise ValueError(f"ERROR {e} while parsing line in .env file: {line}")
