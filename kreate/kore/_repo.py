from typing import Mapping
#import requests
import zipfile
import io
import pkgutil
import logging
import importlib
from pathlib import Path
from ._core import deep_update, DeepChain
#from ..krypt import KryptKonfig, krypt_functions

logger = logging.getLogger(__name__)


class FileGetter:
    def __init__(self, konfig):
        self.konfig = konfig

    def get_data(self, file: str, dir=".") -> str:
        orig_file =file
        dekrypt = False

        if file.startswith("dekrypt:"):
           dekrypt = True
           file = file[8:]
        if file.startswith("repo:"):
            data, basedir = self.load_repo_data(file[5:])
        elif file.startswith("py:"):
            data, basedir = self.load_package_data(file[3:])
        else:
            data, basedir = self.load_file_data(file, dir=dir)
        if dekrypt:
            logger.warning(f"dekrypt not implemented for {orig_file}")
        return data, basedir

    def load_file_data(self, filename: str, dir: str) -> (str, str):
        logger.debug(f"loading file {filename} ")
        p = Path(dir, filename)
        return p.read_text(), p.parent

    def load_repo_data(self, filename: str) -> (str, str):
        repo = filename.split(":")[0]
        filename = filename[len(repo)+1:]
        logger.warning(f"loading file {filename} from repo {repo} NOT implemented")
        p = Path(self.konfig.dir, filename)
        return p.read_text(), p.parent

    def load_package_data(self, filename: str) -> (str, str):
        package_name = filename.split(":")[0]
        filename = filename[len(package_name)+1:]
        package = importlib.import_module(package_name)
        logger.debug(f"loading file {filename} from package {package_name}")
        data = pkgutil.get_data(package.__package__, filename)
        return data.decode("utf-8"), "TODO"
