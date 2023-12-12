from typing import Protocol, Union, TYPE_CHECKING, Mapping
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
from ._core import wrap


if TYPE_CHECKING:  # Only imports the below statements during type checking
    from kreate.kore._konfig import Konfig

logger = logging.getLogger(__name__)


def cache_dir():
    cache_dir = os.getenv("KREATE_REPO_CACHE_DIR")
    if not cache_dir:
        cache_dir = Path.home() / ".cache/kreate/repo"
    return Path(cache_dir)


def clear_cache(_=None):
    """clear the repo cache"""
    logger.warning(f"removing repo cache dir {cache_dir()}")
    if cache_dir().is_dir():
        shutil.rmtree(cache_dir())


class FileGetter:
    def __init__(self, konfig: "Konfig", main_dir_path: Path):
        self.konfig = konfig
        self.repo_prefixes = {
            # "main_konfig:": FixedDirRepo(dir),
            "cwd": FixedDirRepo(Path.cwd()),
            "home": FixedDirRepo(Path.home()),
        }
        self.repo_types = {
            "url-zip:": UrlZipRepo,
            "local-dir:": LocalKonfigRepo,
            "local-zip:": LocalZipRepo,
            "bitbucket-zip:": BitbucketZipRepo,
            "bitbucket-file:": BitbucketFileRepo,
            "python-package:" : PythonPackageRepo,
        }
        # self.reponame = None # TODO: remove self.split_location(location)
        self.main_dir_path = main_dir_path

    def __str__(self) -> str:
        return f"FileGetter({self.main_dir_path=})"

    def konfig_repos(self):
        for repo in self.konfig.get_path("system.repo", []):
            self.repo_prefixes[repo] = self.get_repo(repo)

    def get_prefix(self, filename: str) -> str:
        if filename.startswith("optional:"):
            filename = filename[9:]
        if filename.startswith("dekrypt:"):
            filename = filename[8:]
        match = re.match("^[a-zA-Z0-9_-]*:", filename)
        if match:
            return match.group()[:-1]
        return ""

    def split_location(self, location: str):
        if match := re.match("^[a-zA-Z0-9_-]*:", location):
            reponame = match.group()[:-1]
            if len(reponame) > 1:
                # length 1 could mean windows drive letter
                filename = location[len(reponame) + 1 :]
                while filename.startswith("/"):
                    filename = filename[1:]
                return reponame, Path(filename)
        return None, Path(location)

    def my_repo(self, reponame=None, optional: bool = False):
        reponame = reponame or self.reponame
        if repo := self.repo_prefixes.get(reponame):
            return repo
        if optional:
            return None
        raise ValueError(f"Could not find repo {reponame}")

    def save_repo_file(self, filename: str, data):
        repo, file = self.split_location(filename)
        if repo:
            self.my_repo(repo).save_repo_file(str(file), data)
        #elif self.reponame:
        #    self.my_repo().save_repo_file(str(self.main_dir_path / file), data)
        else:
            logger.info(f"saving data to {self.main_dir_path / file}")
            with open(self.main_dir_path / file, "w") as f:
                f.write(data)

    def get_data(self, file: str) -> str:
        orig_file = file
        reponame = None
        dekrypt = False
        optional = False
        if file.startswith("optional:"):
            optional = True
            file = file[9:]
        if file.startswith("dekrypt:"):
            dekrypt = True
            file = file[8:]
        reponame, path = self.split_location(file)
        if reponame:
            repo = self.my_repo(reponame, optional=optional)
            if not repo and optional:
                logger.warning(
                    f"WARNING: could not find repo {reponame}, for optional file {file}"
                )
                return ""
            data = repo.get_data(path, optional=optional)
        else:
            logger.debug(f"looking for {file} in {path}")
            data = self.load_file_data(path)
        if data is None:
            if optional:
                logger.debug(f"ignoring missing optional file {orig_file}")
                return None
            else:
                raise FileNotFoundError(
                    f"non-optional file {orig_file} does not exist in {self.main_dir_path}"
                )
        logger.debug(f"loaded {file}")
        if dekrypt:
            logger.debug(f"dekrypting {file}")
            data = self.konfig.dekrypt_str(data)
        return data

    def load_file_data(self, filename: Path) -> str:
        path = self.main_dir_path / filename
        if not path.exists():
            logger.debug(f"skipping file {filename} ")
            return None
        logger.debug(f"loading file {filename} ")
        return path.read_text()

    def get_repo(self, repo_name: str):
        repo_konf : Mapping = self.konfig.get_path(f"system.repo.{repo_name}", {})
        type = repo_konf.get("type", None)
        if type == "local-dir":
            return LocalKonfigRepo(self.konfig, repo_name, repo_konf)
        elif type == "local-zip":
            return LocalZipRepo(self.konfig, repo_name, repo_konf)
        elif self.use_local_dir(repo_name):
            return LocalKonfigRepo(self.konfig, repo_name, repo_konf)
        elif type == "url-zip":
            return UrlZipRepo(self.konfig, repo_name, repo_konf)
        elif type == "bitbucket-zip":
            return BitbucketZipRepo(self.konfig, repo_name, repo_konf)
        elif type == "bitbucket-file":
            return BitbucketFileRepo(self.konfig, repo_name, repo_konf)
        elif type == "python-package":
            return PythonPackageRepo(self.konfig, repo_name, repo_konf)
        else:
            raise ValueError(f"Unknown repo type {type} for repo {repo_name}")

    def use_local_dir(self, repo_name: str) -> bool:
        postfix = repo_name.upper().replace("-", "_")
        use = os.getenv("KREATE_REPO_USE_LOCAL_DIR", "False")
        use = os.getenv("KREATE_REPO_USE_LOCAL_DIR_" + postfix, use)
        return use == "True"


class Repo(Protocol):
    def get_data(self, path: Path, optional: bool = False) -> str:
        ...

    def save_repo_file(self, filename: str) -> Path:
        raise NotImplementedError(
            f"not possible to save file in repo {self.__class__}: {filename}"
        )


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
    def __init__(self, konfig: "Konfig", repo_name: str, repo_konf: Mapping):
        self.konfig = konfig
        self.repo_name = repo_name
        self.repo_konf = wrap(
            repo_konf or konfig.get_path("system.repo." + repo_name)
        )
        self.version = self.repo_konf.get("version", None)
        if not self.version:
            raise ValueError(f"no version given for repo {repo_name}")
        self.version = str(self.version)  # sometimes a version is a float like 0.1

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.repo_name}, version={self.version})"

    def download(self, filename: str) -> bool:
        raise FileNotFoundError(f"Could not find {self.calc_dir()}/{filename} in repo {self.repo_name}")

    def get_data(self, filename: Path, optional: bool = False):
        if isinstance(self.version, str) and self.version.startswith("branch."):
            version = self.version[7:]
            if self.repo_konf.get("show_branch_warning", True):
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
        logger.debug(f"getting data from {p}")
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


class PythonPackageRepo(KonfigRepo):
    def get_data(self, filename: Path, optional: bool = False):
        package_name = self.repo_konf.get_path("package", mandatory=True)
        path = Path(self.repo_konf.get("path"))
        filename = str(path / filename)
        package = importlib.import_module(package_name)
        logger.debug(f"loading file {filename} from package {package_name}")
        try:
            data : bytes = pkgutil.get_data(package.__package__, filename)
        except FileNotFoundError as e:
            if optional:
                return ""
            raise
        if data is None:
            raise FileNotFoundError(f"could not find {filename} in module {package_name}")
        return data.decode()


class LocalKonfigRepo(KonfigRepo):
    def calc_local_dir(self) -> str:
        postfix = self.repo_name.upper().replace("-", "_")
        dir = os.getenv("KREATE_REPO_LOCAL_DIR", "..")
        dir = os.getenv("KREATE_REPO_LOCAL_DIR_" + postfix, dir)
        self.konfig.tracer.push(f"formatting repo {self.repo_name} dir: {dir}")
        dir = dir.format(
            my=self,
            konfig=self.konfig,
            app=self.konfig.get_path("app"),
            env=self.konfig.get_path("app.env"),
            appname=self.konfig.get_path("app.appname"),
        )
        self.konfig.tracer.pop()
        return dir

    def calc_dir(self):
        dir: str = self.calc_local_dir()
        dir = self.repo_konf.get("dir", dir)
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
        logger.info(
            f"could not find {self.calc_url(filename)}, marking it to prevent future attempts"
        )
        marker_path.touch()
        return False


def unzip(
    zfile: zipfile.ZipFile,
    dir: Path,
    skip_levels: int = 0,
    select_regexp: str = None,
):
    if skip_levels == 0 and not select_regexp:
        logger.info(f"extracting all files to {dir}")
        zfile.extractall(dir)
        return
    logger.info(f"extracting files to {dir} with pattern {select_regexp}")
    for fname in zfile.namelist():
        newname = "/".join(fname.split("/")[skip_levels:])
        if newname and re.match(select_regexp, fname):
            newpath = dir / newname
            if fname.endswith("/"):
                logger.verbose(f"extracting dir  {newname}")
                newpath.mkdir(parents=True, exist_ok=True)
            else:
                logger.verbose(f"extracting file {newname}")
                newpath.parent.mkdir(parents=True, exist_ok=True)
                newpath.write_bytes(zfile.read(fname))
        else:
            logger.debug(f"skipping not selected {fname} ")
