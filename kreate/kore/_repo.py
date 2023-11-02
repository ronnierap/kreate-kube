from typing import Protocol, Union
import requests
import requests.auth
import zipfile
import hashlib
import io
import os
import re
import pkgutil
import shutil
import logging
import importlib
import warnings
from pathlib import Path

logger = logging.getLogger(__name__)


def cache_dir():
    cache_dir = os.getenv("KREATE_REPO_CACHE_DIR")
    if not cache_dir:
        cache_dir = Path.home() / ".cache/kreate/repo"
    return Path(cache_dir)


def clear_cache():
    logger.warning(f"removing repo cache dir {cache_dir()}")
    if cache_dir().is_dir():
        shutil.rmtree(cache_dir())


class FileGetter:
    def __init__(self, konfig, location: str):
        self.konfig = konfig
        self.repo_prefixes = {
            #"main_konfig:": FixedDirRepo(dir),
            "cwd": FixedDirRepo(Path.cwd()),
            "home": FixedDirRepo(Path.home()),
            #"py:": PythonPackageRepo(),
        }
        self.repo_types = {
            "url-zip:": UrlZipRepo,
            "local-dir:": LocalKonfigRepo,
            "local-zip:": LocalZipRepo,
            "bitbucket-zip:": BitbucketZipRepo,
            "bitbucket-file:": BitbucketFileRepo,
        }
        self.reponame, dir = self.split_location(location)
        self.dir = Path(dir).parent

    def __str__(self) -> str:
        return f"FileGetter({self.reponame=}, {self.dir=})"

    def konfig_repos(self):
        for repo in self.konfig.get_path("system.repo", []):
            self.repo_prefixes[repo ] = self.get_repo(repo)

    def get_prefix(self, filename: str) -> str:
        if filename.startswith("optional:"):
            filename = filename[9:]
        if filename.startswith("dekrypt:"):
            filename = filename[8:]
        match = re.match("^[a-zA-Z0-9_-]*:", filename)
        if match:
            return match.group()[:-1]
        return self.reponame

    def split_location(self, location: str):
        if match := re.match("^[a-zA-Z0-9_-]*:", location):
            reponame = match.group()[:-1]
            if len(reponame) > 1:
                # length 1 could mean windows drive letter
                filename = location[len(reponame)+1:]
                while filename.startswith("/"):
                    filename = filename[1:]
                return reponame, Path(filename)
        return None, Path(location)

    def my_repo(self, reponame=None):
        reponame = reponame or self.reponame
        if repo := self.repo_prefixes.get(reponame):
            return repo
        raise ValueError(f"Could not find repo {reponame}")

    def save_repo_file(self, filename: str, data):
        repo, file = self.split_location(filename)
        if repo:
           repo.save_repo_file(file)
        elif self.reponame:
            self.my_repo().save_repo_file(self.dir / file)
        else:
            logger.info(f"saving data to {self.dir / file}")
            with open(self.dir / file, "w") as f:
                f.write(data)

    def get_data(self, file: str) -> str:
        orig_file = file
        repo = None
        dekrypt = False
        optional = False
        if file.startswith("optional:"):
            optional = True
            file = file[9:]
        if file.startswith("dekrypt:"):
            dekrypt = True
            file = file[8:]
        repo, path = self.split_location(file)
        if repo:
            data = self.my_repo(repo).get_data(path, optional=optional)
        elif self.reponame:
            data = self.my_repo().get_data(self.dir / path, optional=optional)
        else:
            data = self.load_file_data(path)
        if data is None:
            if optional:
                logger.debug(f"ignoring optional file {orig_file}")
                return ""
            else:
                raise FileNotFoundError(f"non-optional file {orig_file} does not exist in {self.dir}")
        logger.info(f"loaded {file}")
        if dekrypt:
            logger.debug(f"dekrypting {file}")
            data = self.konfig.dekrypt_bytes(data)
        return data

    def kopy_file(self, loc: str, target: Path) -> None:
        logger.info(f"kopying file {loc} to {target}")
        data = self.get_data(loc)
        dir = target.parent
        dir.mkdir(parents=True, exist_ok=True)
        if isinstance(data, bytes):
            data = data.decode()
        target.write_text(data)

    def load_file_data(self, filename: Path) -> str:
        logger.debug(f"loading file {filename} ")
        path = self.dir / filename
        if not path.exists():
            return None
        return path.read_text()

    def get_repo(self, repo_name: str):
        type = self.konfig.get_path(f"system.repo.{repo_name}.type", None)
        if type == "url-zip":
            return UrlZipRepo(self.konfig, repo_name)
        elif type == "local-dir":
            return LocalKonfigRepo(self.konfig, repo_name)
        elif type == "local-zip":
            return LocalZipRepo(self.konfig, repo_name)
        elif type == "bitbucket-zip":
            return BitbucketZipRepo(self.konfig, repo_name)
        elif type == "bitbucket-file":
            return BitbucketFileRepo(self.konfig, repo_name)
        else:
            raise ValueError(f"Unknown repo type {type} for repo {repo_name}")


class Repo(Protocol):
    def get_data(self, path: Path, optional: bool = False) -> str:
        ...

    def save_repo_file(self, filename: str) -> Path:
        raise NotImplementedError(f"not possible to save file in repo {self.__class__}: {filename}")


class PythonPackageRepo(Repo):
    def get_data(self, filename: str, optional: bool = False) -> str:
        package_name = filename.split(":")[0]
        filename = filename[len(package_name) + 1 :]
        package = importlib.import_module(package_name)
        logger.debug(f"loading file {filename} from package {package_name}")
        data = pkgutil.get_data(package.__package__, filename)
        return data.decode("utf-8")


class FixedDirRepo(Repo):
    def __init__(self, dir: Union[Path, str]):
        if isinstance(dir, str):
            self.dir = Path(dir)
        elif isinstance(dir, Path):
            self.dir = dir
        else:
            raise TypeError(f"Unsupported type {type(dir)}, {dir}")

    def save_repo_file(self, filename: str, data) -> Path:
        while filename.startswith("/"):
            filename = filename[1:]
        logger.info(f"saving data in FixedDirRepo to {self.dir / filename}")
        with open(self.dir / filename, "w") as f:
            f.write(data)

    def get_data(self, filename: Path, optional: bool = False):
        path = self.dir / filename
        if not path.exists():
            raise FileNotFoundError(f"could not find file {filename} in {dir}")
        return path.read_text()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.dir})"


class KonfigRepo(Repo):
    def __init__(self, konfig, repo_name: str):
        self.konfig = konfig
        self.repo_name = repo_name
        self.repo_konf = konfig.get_path("system.repo." + repo_name)
        self.version = self.repo_konf.get("version", None)
        if not self.version:
            raise ValueError(f"no version given for repo {repo_name}")
        self.version = str(self.version)  # sometimes a version is a float like 0.1

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.repo_name}, version={self.version})"

    def download(self, filename: str) -> bool:
        raise NotImplementedError(f"Could not download {self.repo_name}")

    def get_data(self, filename: Path, optional: bool = False):
        if isinstance(self.version, str) and self.version.startswith("branch."):
            version = self.version[7:]
            warnings.warn(
                f"Using branch {version} for repo {self.repo_name} is not recommended, use a tag instead"
            )
        if optional and self.repo_konf.get("disabled", False):
            logger.info(
                f"skipping optional {filename} in disable repo {self.repo_name}"
            )
            return ""
        dir = Path(self.calc_dir())
        if not dir.exists():
            self.download(filename)
        if not dir.is_dir():
            # add other assertions, or better error message?
            raise FileExistsError(f"repo dir {dir} exists, but is not a directory")
        p = dir / filename
        if not p.exists():
            if not self.download_extra_file(filename):
                if optional:
                    return ""
                raise FileNotFoundError(f"could not find file {filename} in {dir}")
        return p.read_text()

    def download_extra_file(self, filename: str) -> bool:
        return False

    def calc_hash(self, extra: str = "") -> str:
        return hashlib.md5(
            (
                self.repo_name
                + str(self.repo_konf.get("version", ""))
                + self.calc_url("...")
                + extra
            ).encode()
        ).hexdigest()[:10]

    def calc_dir(self) -> Path:
        hash = self.calc_hash()
        dir = self.repo_konf.get("cache_name")
        if dir:
            if self.version:
                return cache_dir() / f"{dir}/{self.version.replace('/','-')}-{hash}"
            return cache_dir() / f"{dir}-{hash}"
        if self.version:
            return (
                cache_dir() / f"{self.repo_name}/{self.version.replace('/','-')}-{hash}"
            )
        else:
            return cache_dir() / f"{self.repo_name}-{hash}"

    def calc_url(self, filename: str) -> str:
        url = self.repo_konf.get("url", "")
        if self.version:
            url = url.replace("{version}", self.version)
        return url

    def unzip_data(self, data) -> None:
        z = zipfile.ZipFile(io.BytesIO(data))
        skip_levels = self.repo_konf.get("skip_levels", 0)
        regexp = self.repo_konf.get("select_regexp", "")
        self.calc_dir().mkdir(parents=True)
        unzip(z, self.calc_dir(), skip_levels=skip_levels, select_regexp=regexp)

    def url_response(self, filename: str, raise_error=True):
        auth = None
        if self.repo_konf.get("basic_auth", {}):
            usr_env_var = self.repo_konf["basic_auth"]["usr_env_var"]
            psw_env_var = self.repo_konf["basic_auth"]["psw_env_var"]
            usr = os.getenv(usr_env_var)
            psw = os.getenv(psw_env_var)
            auth = requests.auth.HTTPBasicAuth(usr, psw)
        url = self.calc_url(filename)
        logger.info(f"downloading {self.calc_dir()} from {url}")
        response = requests.get(url, auth=auth)
        if response.status_code >= 300 and raise_error:
            raise IOError(
                f"status {response.status_code} while downloading {url} with message {response.content}"
            )
        return response


class LocalKonfigRepo(KonfigRepo):
    def calc_dir(self):
        dir: str = self.repo_konf.get("dir")
        if self.version:
            dir = dir.replace("{version}", self.version)
        return Path(dir)

    def save_repo_file(self, filename: str, data):
        while filename.startswith("/"):
            filename = filename[1:]
        with open(self.calc_dir() / filename, "w") as f:
            f.write(data)


class LocalZipRepo(KonfigRepo):
    def download(self, filename: str) -> bool:
        path: str = self.repo_konf.get("path")
        if self.version:
            path = path.replace("{version}", self.version)
        logger.info(f"unzipping {self.calc_dir()} from {path}")
        data = Path(path).read_bytes()
        self.unzip_data(data)
        return True


class UrlZipRepo(KonfigRepo):
    def download(self, filename: str) -> bool:
        data = self.url_response(filename).content
        self.unzip_data(data)
        return True


class BitbucketZipRepo(KonfigRepo):
    def download(self, filename: str) -> bool:
        data = self.url_response(filename).content
        self.unzip_data(data)
        return True

    def calc_url(self, filename: str) -> str:
        return self._calc_url("archive", "&format=zip")

    def _calc_url(self, ext: str, format: str = "") -> str:
        url = self.repo_konf.get("url", None)
        url += f"/{ext}"
        if self.version.startswith("branch."):
            version = self.version[7:]
            url += f"?at=refs/heads/{version}" + format
        else:
            url += f"?at=refs/tags/{self.version}" + format
        return url


class BitbucketFileRepo(BitbucketZipRepo):
    def download(self, filename: str, raise_error=True) -> bool:
        response = self.url_response(filename, raise_error=raise_error)
        if response.status_code > 300:
            return False
        path = self.calc_dir() / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(response.content)
        return True

    def calc_url(self, filename: str) -> str:
        filename = str(filename)
        while filename.startswith("/"):
            filename = filename[1:]
        return self._calc_url(f"raw/{filename}")

    def download_extra_file(self, filename: str) -> bool:
        """check if it was previous attempted to download this file"""
        marker_path = self.calc_dir() / f"{filename}.does-not-exist"
        if marker_path.exists():
            return False
        if self.download(filename, raise_error=False):
            return True
        logger.info(f"could not find {self.calc_url(filename)}, marking it to prevent future attempts")
        marker_path.touch()
        return False


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
