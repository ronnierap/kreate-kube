from typing import Mapping
import requests
import zipfile
import io
import os
import re
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
            data = self.load_repo_data(file[5:])
        elif file.startswith("py:"):
            data = self.load_package_data(file[3:])
        else:
            data = self.load_file_data(file, dir=dir)
        if dekrypt:
            logger.warning(f"WARNING: dekrypt not implemented for {orig_file}")
        return data

    def load_file_data(self, filename: str, dir: str) -> str:
        logger.debug(f"loading file {filename} ")
        p = Path(dir, filename)
        return p.read_text()

    def load_repo_data(self, filename: str) -> str:
        repo = filename.split(":")[0]
        dir = self.repo_dir(repo)
        filename = filename[len(repo)+1:]
        p = Path(self.konfig.dir, filename)
        return p.read_text()

    def load_package_data(self, filename: str) -> str:
        package_name = filename.split(":")[0]
        filename = filename[len(package_name)+1:]
        package = importlib.import_module(package_name)
        logger.debug(f"loading file {filename} from package {package_name}")
        data = pkgutil.get_data(package.__package__, filename)
        return data.decode("utf-8")

    def repo_dir(self, repo_name: str) -> Path:
        cache_dir = os.getenv("KREATE_REPO_CACHE_DIR")
        if not cache_dir:
            cache_dir = Path.home() / ".cache/kreate/repo"
        repo_konf = self.konfig.yaml["repo"].get(repo_name, {})
        version = repo_konf.get("version", None)
        if not version:
            raise ValueError(f"no version specified for repo {repo_name}")
        repo_dir = cache_dir / f"{repo_name}-{version}"
        if not repo_dir.exists():
            self.download_repo(repo_name, version, repo_dir)
        if not repo_dir.is_dir():
            raise FileExistsError(f"repo dir {repo_dir} exists, but is not a directory")
        return repo_dir

    def download_repo(self, repo_name: str, version: str, repo_dir: Path):
        repo_konf = self.konfig.yaml["repo"].get(repo_name, {})
        url : str = repo_konf.get("url")
        url.replace("{version}", version)
        logger.info(f"downloading {repo_name}-{version} from {url}")
        #req = requests.get(url)
        #z = zipfile.ZipFile(io.BytesIO(req.content))
        z = zipfile.ZipFile("0.3.0.zip","r")
        repo_dir.mkdir(parents=True)
        unzip(z, repo_dir, skip_levels=3, select_regexp=".*_templates/.*yaml")

def unzip(zfile: zipfile.ZipFile, repo_dir: Path, skip_levels: int = 0, select_regexp : str = None):
    if skip_levels == 0 and not select_regexp:
        zfile.extractall(repo_dir)
        return
    for fname in zfile.namelist():
        newname = "/".join(fname.split("/")[skip_levels:])
        if (re.match(select_regexp, fname)):
            newpath = repo_dir / newname
            if fname.endswith("/"):
                logger.info(f"extracting dir  {newname}")
                newpath.mkdir(parents=True, exist_ok=True)
            else:
                logger.info(f"extracting file {newname}")
                newpath.parent.mkdir(parents=True, exist_ok=True)
                newpath.write_bytes(zfile.read(fname))
        else:
            logger.debug(f"skipping not selected {fname} ")
