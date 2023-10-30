"""
a very simple loader of .env file as environment variables

it seemed overkill to install the dotenv package just for
this functionality
"""

import os
import warnings
from pathlib import Path


def load_env(path: Path, mandatory: bool = False) -> None:
    if not path.is_file():
        if not mandatory:
            return
        raise FileNotFoundError(f"Could not find mandatory env file {path}")
    with open(path) as file:
        lines = [line.strip() for line in file]

    for idx, line in enumerate(lines):
        #try:
            if line.startswith("#") or len(line.strip()) == 0:
                continue
            if "+=" in line and line.index("+=",) < line.index('='):
                k, v = line.split("+=", 1)
                orig_value = os.environ.get(k.strip(),"")
                add_value = " " + v.strip() if orig_value else v.strip()
                os.environ[k.strip()] = orig_value + add_value
            elif "=" in line:
                k, v = line.split("=", 1)
                if k not in os.environ:
                    os.environ[k.strip()] = v.strip()
            else:
                warnings.warn(f"ignore dotenv line {path}:{idx}: {line}", SyntaxWarning)
        #except Exception as e:
        #    raise ValueError(f"ERROR {e} while parsing line in .env file: {line}")
