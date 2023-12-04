"""
a very simple loader of .env file as environment variables

it seemed overkill to install the dotenv package just for
this functionality
"""

import os
import warnings
from pathlib import Path


def load_env(path: Path, mandatory: bool = False) -> None:
    # TODO: logging, but this is loaded before logging
    # might be defined (by command line options in KREATE_OPTIONS)
    if not path.is_file():
        if not mandatory:
            return
        raise FileNotFoundError(f"Could not find mandatory env file {path}")
    with open(path) as file:
        lines = [line.strip() for line in file]

    for idx, line in enumerate(lines):
        # try:
        if line.startswith("#") or len(line.strip()) == 0:
            continue
        elif line.startswith("inklude "):
            # TODO: handle optional and absolute paths
            file = line[8:]
            newpath = path.parent / file
            if newpath.exists():
                load_env(newpath, mandatory=True)
            else:
                raise FileNotFoundError(
                    f"could not inklude env file f{newpath} from {path}"
                )
        elif "+=" in line and line.index(
            "+=",
        ) < line.index("="):
            # append to existing value with space as separator
            k, v = line.split("+=", 1)
            orig_value = os.environ.get(k.strip(), "")
            add_value = " " + v.strip() if orig_value else v.strip()
            os.environ[k.strip()] = orig_value + add_value
        elif ",=" in line and line.index(
            ",=",
        ) < line.index("="):
            # append to existing value with comma as separator
            k, v = line.split(",=", 1)
            orig_value = os.environ.get(k.strip(), "")
            add_value = "," + v.strip() if orig_value else v.strip()
            os.environ[k.strip()] = orig_value + add_value
        elif ":=" in line and line.index(
            ":=",
        ) < line.index("="):
            # overwrite
            k, v = line.split(":=", 1)
            os.environ[k.strip()] = orig_value + add_value
        elif "?=" in line and line.index(
            "?=",
        ) < line.index("="):
            # only use as not set (same as =)
            k, v = line.split("?=", 1)
            if k not in os.environ:
                os.environ[k.strip()] = v.strip()
        elif "=" in line:
            # only use as not set (same as ?=)
            # might be deprecated, since ?= is more explicit
            k, v = line.split("=", 1)
            if k not in os.environ:
                os.environ[k.strip()] = v.strip()
        else:
            warnings.warn(f"ignore dotenv line {path}:{idx}: {line}", SyntaxWarning)
    # except Exception as e:
    #    raise ValueError(f"ERROR {e} while parsing line in .env file: {line}")
