from typing import Mapping
import requests
import requests.auth
import zipfile
import io
import os
import re
import pkgutil
import shutil
import logging
import importlib
from pathlib import Path

logger = logging.getLogger(__name__)


def cache_dir():
    cache_dir = os.getenv("KREATE_REPO_CACHE_DIR")
    if not cache_dir:
        cache_dir = Path.home() / ".cache/kreate/repo"
    return cache_dir


def clear_cache():
    logger.info(f"removing repo cache dir {cache_dir()}")
    shutil.rmtree(cache_dir())


class FileGetter:
    def __init__(self, konfig, dir: str):
        self.konfig = konfig
        self.dir = Path(dir)

    def get_data(self, file: str) -> str:
        orig_file = file
        dekrypt = False
        optional = False
        if file.startswith("optional:"):
            optional = True
            file = file[9:]
        if file.startswith("dekrypt:"):
            dekrypt = True
            file = file[8:]
        if file.startswith("repo:"):
            data = self.load_repo_data(file[5:])
        elif file.startswith("py:"):
            data = self.load_package_data(file[3:])
        elif file.startswith("konf:"):
            data = self.load_file_data(file[5:])
        elif file.startswith("cwd:"):
            data = self.load_file_data(Path.cwd() / file[4:])
        elif file.startswith("home:"):
            data = self.load_file_data(Path.home() / file[5:])
        elif file.startswith("./"):
            data = self.load_file_data(file)
        elif file.startswith("../"):
            data = self.load_file_data(file)
        elif re.match("\w\w+:", file):
            data = self.load_repo_data(file)
        else:
            data = self.load_file_data(file)
        if data is None:
            if optional:
                logger.debug(f"ignoring optional file {orig_file}")
                return ""
            else:
                raise FileExistsError(f"non-optional file {orig_file} does not exist")
        if dekrypt:
            logger.debug(f"dekrypting {file}")
            data = self.konfig.dekrypt_bytes(data)
        return data

    def kopy_file(self, loc: str, target: Path) -> None:
        data = self.get_data(loc)
        dir = target.parent
        dir.mkdir(parents=True, exist_ok=True)
        if isinstance(data, bytes):
            data = data.decode()
        target.write_text(data)

    def load_file_data(self, filename: str) -> str:
        logger.debug(f"loading file {filename} ")
        path = self.dir / filename
        if not path.exists():
            return None
        return path.read_text()

    def load_package_data(self, filename: str) -> str:
        package_name = filename.split(":")[0]
        filename = filename[len(package_name) + 1 :]
        package = importlib.import_module(package_name)
        logger.debug(f"loading file {filename} from package {package_name}")
        data = pkgutil.get_data(package.__package__, filename)
        return data.decode("utf-8")

    def load_repo_data(self, filename: str) -> str:
        repo = self.get_repo(filename)
        return repo.get_data()
        #if not repo_dir.is_dir():
        #    # add other assertions, or better error message?
        #    raise FileExistsError(f"repo dir {repo_dir} exists, but is not a directory")
        #p = Path(dir, filename)
        #if not p.exists():
        #    return None
        #return p.read_text()

    def get_repo(self, filename: str):
        repo_name = filename.split(":")[0]
        filename = filename[len(repo_name) + 1 :]
        type = self.konfig.yaml.get(f"system.repo.{repo_name}.type", None)
        if type == "url-zip":
            return UrlZipRepo(self.konfig, repo_name, filename)
        elif type == "local-dir":
            return LocalDirRepo(self.konfig, repo_name, filename)
        elif type == "local-zip":
            return LocalZipRepo(self.konfig, repo_name, filename)
        elif type == "bitbucket-zip":
            return BitbucketZipRepo(self.konfig, repo_name, filename)
        elif type == "bitbucket-file":
            return BitbucketFileRepo(self.konfig, repo_name, filename)
        else:
            raise ValueError(f"Unknow repo type {type} for repo {repo_name}:{filename}")

class BaseRepo:
    def __init__(self, konfig, repo_name: str, filename: str):
        self.konfig = konfig
        self.repo_name = repo_name
        self.filename = filename
        self.repo_konf = konfig.yaml.get("system.repo." + repo_name, {})
        self.version = self.repo_konf.get("version", None)
        self.repo_dir = self.calc_repo_dir()

    def get_data(self):
        if not self.repo_dir.exists():
            self.download()
        if not self.repo_dir.is_dir():
            # add other assertions, or better error message?
            raise FileExistsError(f"repo dir {self.repo_dir} exists, but is not a directory")
        p = self.repo_dir / self.filename
        if not p.exists():
            raise FileNotFoundError(f"could not find file {self.filename} in {self.repo_dir}")
        return p.read_text()

    def download(self):
        pass

    def calc_repo_dir(self) -> Path:
        if self.version:
            return cache_dir() / f"{self.repo_name}-{self.version}"
        else:
            return cache_dir() / f"{self.repo_name}"

    def calc_url(self):
        url = self.repo_konf.get("url", None)
        if self.version:
            url = url.replace("{version}", self.version)
        return url

    def unzip_data(self, data) -> None:
        z = zipfile.ZipFile(io.BytesIO(data))
        skip_levels = self.repo_konf.get("skip_levels", 0)
        regexp = self.repo_konf.get("select_regexp", "")
        self.repo_dir.mkdir(parents=True)
        unzip(z, self.repo_dir, skip_levels=skip_levels, select_regexp=regexp)

    def url_response(self):
        auth = None
        if self.repo_konf.get("basic_auth", {}):
            usr_env_var = self.repo_konf["basic_auth"]["usr_env_var"]
            psw_env_var = self.repo_konf["basic_auth"]["psw_env_var"]
            usr = os.getenv(usr_env_var)
            psw = os.getenv(psw_env_var)
            auth = requests.auth.HTTPBasicAuth(usr, psw)
        url = self.calc_url()
        logger.info(f"downloading {self.repo_dir} from {url}")
        response = requests.get(url, auth=auth)
        if response.status_code >= 300:
            raise IOError(
                f"status {response.status_code} while downloading {url} with message {response.content}"
            )
        return response

class LocalDirRepo(BaseRepo):
    def calc_repo_dir(self):
        dir: str = self.repo_konf.get("dir")
        if self.version:
            dir = dir.replace("{version}", self.version)
        return Path(dir)


class LocalZipRepo(BaseRepo):
    def download(self):
        path: str = self.repo_konf.get("path")
        if self.version:
            path = path.replace("{version}", self.version)
        logger.info(f"unzipping {self.repo_dir} from {path}")
        data = Path(path).read_bytes()
        self.unzip_data(data)


class UrlZipRepo(BaseRepo):
    def download(self):
            data = self.url_response().content
            self.unzip_data(data)


class BitbucketZipRepo(BaseRepo):
    def download(self):
        data = self.url_response().content
        self.unzip_data(data)

    def calc_url(self) -> str:
        return self._calc_url("archive", "&format=zip")

    def _calc_url(self, ext: str, format:str = "") -> str:
        url = self.repo_konf.get("url", None)
        url += f"/{ext}"
        if self.version.startswith("branch."):
            version = self.version[7:]
            logger.warning(
                f"Using branch {version} as version is not recommended, use a tag instead"
            )
            url += f"?at=refs/heads/{version}" + format
        else:
            url += f"?at=refs/tags/{self.version}" + format
        bitbucket_project = self.repo_konf.get("bitbucket_project")
        bitbucket_repo = self.repo_konf.get("bitbucket_repo")
        if bitbucket_project:
            url = url.replace("{project}", bitbucket_project)
        if bitbucket_repo:
            url = url.replace("{repo}", bitbucket_repo)
        return url

class BitbucketFileRepo(BitbucketZipRepo):
    def download(self):
        content = self.url_response().content
        path = self.calc_repo_dir() / self.filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def calc_repo_dir(self) -> Path:
        bitb_project = self.repo_konf.get("bitbucket_project")
        bitb_repo = self.repo_konf.get("bitbucket_repo")
        version = self.version.replace("/", "-")
        return cache_dir() / f"{self.repo_name}-{bitb_project}-{bitb_repo}/{version}"

    def calc_url(self) -> str:
        return self._calc_url(f"raw/{self.filename}")

def unzip(
    zfile: zipfile.ZipFile,
    dir: Path,
    skip_levels: int = 0,
    select_regexp: str = None,
):
    if skip_levels == 0 and not select_regexp:
        zfile.extractall(dir)
        return
    for fname in zfile.namelist():
        newname = "/".join(fname.split("/")[skip_levels:])
        if newname and re.match(select_regexp, newname):
            newpath = dir / newname
            if fname.endswith("/"):
                logger.info(f"extracting dir  {newname}")
                newpath.mkdir(parents=True, exist_ok=True)
            else:
                logger.info(f"extracting file {newname}")
                newpath.parent.mkdir(parents=True, exist_ok=True)
                newpath.write_bytes(zfile.read(fname))
        else:
            logger.debug(f"skipping not selected {fname} ")
