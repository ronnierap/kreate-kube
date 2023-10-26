import os
import logging
import importlib.metadata
from pathlib import Path
from typing import List, Set
from packaging.specifiers import SpecifierSet
from packaging.version import Version, InvalidVersion

from ._core import deep_update, wrap
from ._repo import FileGetter
from ._jinyaml import JinYaml


logger = logging.getLogger(__name__)


class Konfig:
    def __init__(self, filename: str = None, dict_: dict = None, inkludes=None):
        konfig_path = self.find_konfig_file(filename)
        logger.info(f"loading main konfig from {konfig_path}")
        self.dir = konfig_path.parent
        self.filename = str(konfig_path)
        self.dekrypt_func = None
        filename = os.path.basename(filename)
        self.dict_ = dict_ or {}
        self.yaml = wrap(self.dict_)
        self.jinyaml = JinYaml(self)
        deep_update(dict_, {"system": {"getenv": os.getenv}})
        self.file_getter = FileGetter(self, self.dir)
        for ink in inkludes or []:
            self.inklude(ink)
        self.inklude(konfig_path.name)
        self.load_all_inkludes()

    def find_konfig_file(self, filename):
        if filename is None:
            filename = os.getenv("KREATE_KONFIG_PATH",".")
        glob_pattern = os.getenv("KREATE_KONFIG_FILE", "kreate*.konf")
        for p in filename.split(os.pathsep):
            path = Path(p)
            if path.is_file():
                return path
            elif path.is_dir():
                logger.debug(f"checking for {glob_pattern} in dir {path}")
                possible_files = tuple(path.glob(glob_pattern))
                if len(possible_files) == 1:
                    return possible_files[0]
                elif len(possible_files) > 1:
                    raise ValueError(
                        f"Ambiguous konfig files found for {path}/{glob_pattern}: {possible_files}"
                    )
        raise ValueError(f"No main konfig file found for {filename}/{glob_pattern}")

    def get_path(self, path: str, default=None):
        return self.yaml._get_path(path, default=default)

    def _jinja_context(self):
        result = {}  # "konf": self, "appname": self.appname, "env": self.env}
        for k in self.yaml.keys():
            v = self.yaml[k]
            result[k] = v
        return result

    def load_repo_file(self, fname: str) -> str:
        return self.file_getter.get_data(fname)

    def load_all_inkludes(self):
        logger.debug("loading inklude files")
        already_inkluded = set()
        inkludes = self.get_path("inklude", [])
        # keep loading inkludes until all is done
        while self.load_inkludes(inkludes, already_inkluded) > 0:
            # possible new inkludes are added
            inkludes = self.get_path("inklude", [])

    def load_inkludes(self, inkludes: List[str], already_inkluded: Set[str]) -> int:
        count = 0
        for idx, fname in enumerate(inkludes):
            if fname not in already_inkluded:
                count += 1
                already_inkluded.add(fname)
                self.inklude(fname, idx + 1)
        logger.debug(f"inkluded {count} new files")
        return count

    def inklude(self, fname: str, idx: int = None):
        logger.info(f"inkluding {fname}")
        # reload all repositories, in case any were added/changed
        self.file_getter.konfig_repos()
        context = self._jinja_context()
        context["my_repo_name"] = self.file_getter.get_prefix(fname)
        val_yaml = self.jinyaml.render(fname, context)
        if val_yaml:  # it can be empty
            deep_update(self.yaml, val_yaml, list_insert_index={"inklude": idx})

    def get_kreate_version(self) -> str:
        try:
            return importlib.metadata.version("kreate-kube")
        except importlib.metadata.PackageNotFoundError:
            return "Unknown"

    def check_kreate_version(self, force: bool = False):
        version = self.get_kreate_version()
        dev_versions = ["Unknown"]  #  , "rc", "editable"]
        if any(txt in version for txt in dev_versions) and not force:
            logger.info(f"skipping check for development version {version}")
            return
        req_version: str = self.get_path("version.kreate_version", None)
        if not req_version:
            logger.info(f"skipping check since no kreate_version specified")
            return
        if not SpecifierSet(req_version).contains(Version(version)):
            raise InvalidVersion(
                f"Invalid kreate version {version} for specifier {req_version}"
            )

    def dekrypt_bytes(b: bytes) -> bytes:
        raise NotImplementedError("dekrypt_bytes not implemented")
