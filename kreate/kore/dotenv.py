"""
a very simple loader of .env file as environment variables

it seemed overkill to install the dotenv package just for
this functionality
"""

import os
from pathlib import Path

def load_dotenv(path: str) -> None:
    if not Path(path).is_file():
        return
    with open(path) as file:
        lines = [line.strip() for line in file]

    for line in lines:
        try:
            if line.startswith("#") or len(line) == 0:
                continue
            k, v = line.split("=", 1)
            if k not in os.environ:
                os.environ[k] = v
        except Exception as e:
            raise ValueError(f"ERROR {e} while parsing line in .env file: {line}")
