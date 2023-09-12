from typing import Mapping
import requests
import requests.auth
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
            logger.debug(f"dekrypting {file}")
            data = self.konfig.dekrypt_bytes(data)
        return data

    def load_file_data(self, filename: str, dir: str) -> str:
        logger.info(f"loading file {filename} ")
        p = Path(dir, filename)
        return p.read_text()

    def load_package_data(self, filename: str) -> str:
        package_name = filename.split(":")[0]
        filename = filename[len(package_name)+1:]
        package = importlib.import_module(package_name)
        logger.info(f"loading file {filename} from package {package_name}")
        data = pkgutil.get_data(package.__package__, filename)
        return data.decode("utf-8")

    def load_repo_data(self, filename: str) -> str:
        repo = filename.split(":")[0]
        dir = self.repo_dir(repo)
        filename = filename[len(repo)+1:]
        p = Path(dir, filename)
        return p.read_text()

    def repo_dir(self, repo_name: str) -> Path:
        repo_konf = self.konfig.yaml["repo"].get(repo_name, {})
        if repo_konf.get("type",None) == "local-dir":
            # special case, does not cache dir
            repo_dir = self.local_dir_repo()
        else:
            repo_dir = self.download_repo(repo_name)
        if not repo_dir.is_dir():
            # add other assertions, or better error message?
            raise FileExistsError(f"repo dir {repo_dir} exists, but is not a directory")
        return repo_dir

    def local_dir_repo(self, repo_konf: Mapping):
        dir = repo_konf["dir"]
        version = repo_konf.get("version", None)
        if version:
            dir = dir.replace("version", version)
        return Path(dir)

    def download_repo(self, repo_name: str):
        cache_dir = os.getenv("KREATE_REPO_CACHE_DIR")
        if not cache_dir:
            cache_dir = Path.home() / ".cache/kreate/repo"
        repo_konf = self.konfig.yaml["repo"].get(repo_name, {})
        version = repo_konf.get("version", None)
        if version:
            repo_dir = cache_dir / f"{repo_name}-{version}"
        else:
            repo_dir = cache_dir / f"{repo_name}"
        if repo_dir.exists():
            # nothing needs to be downloaded, maybe extra checks needed?
            return repo_dir
        type = repo_konf.get("type", "url-zip")
        if type == "url-zip":
            data = self.url_data(repo_dir, repo_konf, version)
            self.unzip_data(repo_dir, repo_konf, data)
        elif type == "bitbucket-zip":
            data = self.bitbucket_data(repo_dir, repo_konf, version)
            self.unzip_data(repo_dir, repo_konf, data)
        elif type == "local-zip":
            data = self.local_path_data(repo_dir, repo_konf, version)
            self.unzip_data(repo_dir, repo_konf, data)
        else:
            raise ValueError(f"Unknow repo type {type} for repo {repo_name}")
        return repo_dir

    def url_data(self, repo_dir, repo_konf, version):
        url : str = repo_konf.get("url")
        auth = None
        if repo_konf.get("basic_auth", {}):
            usr_env_var = repo_konf["basic_auth"]["usr_env_var"]
            psw_env_var = repo_konf["basic_auth"]["psw_env_var"]
            usr = os.getenv(usr_env_var)
            psw = os.getenv(psw_env_var)
            auth = requests.auth.HTTPBasicAuth(usr, psw)
        if version:
            url = url.replace("{version}", version)
        logger.info(f"downloading {repo_dir} from {url}")
        response = requests.get(url, auth=auth)
        if response.status_code >= 300:
            raise IOError(f"status {response.status_code} while downloading {url} with message {response.content}")
        return response.content

    def bitbucket_data(self, repo_dir, repo_konf, version):
        if version == "master":
            version = f"refs/heads/{version}"
        else:
            version = f"refs/tags/{version}"
        return self.url_data(repo_dir, repo_konf, version)

    def local_path_data(self, repo_dir, repo_konf, version):
        path : str = repo_konf.get("path")
        if version:
            path = path.replace("{version}", version)
        logger.info(f"unzipping {repo_dir} from {path}")
        return Path(path).read_bytes()

    def unzip_data(self, repo_dir: str, repo_konf: Mapping, data) -> None:
        z = zipfile.ZipFile(io.BytesIO(data))
        skip_levels  = repo_konf.get("skip_levels", 0)
        regexp = repo_konf.get("select_regexp", "")
        repo_dir.mkdir(parents=True)
        unzip(z, repo_dir, skip_levels=skip_levels, select_regexp=regexp)



def unzip(zfile: zipfile.ZipFile, repo_dir: Path, skip_levels: int = 0, select_regexp : str = None):
    if skip_levels == 0 and not select_regexp:
        zfile.extractall(repo_dir)
        return
    for fname in zfile.namelist():
        newname = "/".join(fname.split("/")[skip_levels:])
        if newname and re.match(select_regexp, newname):
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
