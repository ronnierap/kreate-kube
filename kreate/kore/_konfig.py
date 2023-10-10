import os
import logging
import pkg_resources
import importlib.metadata
from pathlib import Path
from typing import List, Set

from ._core import deep_update, wrap
from ._repo import FileGetter
from ._jinyaml import JinYaml


logger = logging.getLogger(__name__)


class Konfig:
    def __init__(self, filename: str = None, dict_: dict = None,
                 inkludes=None):
        filename = filename or "konfig.yaml"
        if os.path.isdir(filename):
            filename += "/konfig.yaml"
        self.filename = filename
        self.dekrypt_func = None
        self.jinyaml = JinYaml(self)
        self.dir = Path(os.path.dirname(filename))
        filename = os.path.basename(filename)
        self.file_getter = FileGetter(self, self.dir)
        dict_ = dict_ or {}
        deep_update(dict_, {"system": { "getenv":  os.getenv}})
        for ink in inkludes or []:
            deep_update(dict_, self.jinyaml.render(ink, dict_))
        deep_update(dict_, self.jinyaml.render(filename, dict_))
        self.yaml = wrap(dict_)
        self.load_all_inkludes()

    # def __iter__(self):
    #    return iter(self.yaml.keys())

    def __getattr__(self, attr):
        if attr == "get":
            return self.yaml.get
        if attr not in self.yaml:
            raise AttributeError(f"could not find attribute {attr} in {self}")
        else:
            return self.yaml[attr]

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
        inkludes = self.yaml.get("inklude", [])
        # keep loading inkludes until all is done
        while self.load_inkludes(inkludes, already_inkluded) > 0:
            # possible new inkludes are added
            inkludes = self.yaml.get("inklude", [])

    def load_inkludes(self, inkludes: List[str], already_inkluded: Set[str]) -> int:
        count = 0
        for fname in inkludes:
            if fname not in already_inkluded:
                count += 1
                already_inkluded.add(fname)
                self.load_inklude(fname)
        logger.debug(f"inkluded {count} new files")
        return count

    def load_inklude(self, fname: str):
        logger.info(f"inkluding {fname}")
        context = self._jinja_context()
        val_yaml = self.jinyaml.render(fname, context)
        if val_yaml:  # it can be empty
            deep_update(self.yaml, val_yaml)

    def get_kreate_version(self) -> str:
        try:
            return importlib.metadata.version("kreate-kube")
        except importlib.metadata.PackageNotFoundError:
            return "Unknown"

    def check_kreate_version(self, force: bool = False):
        version = self.get_kreate_version()
        dev_versions = [ "Unknown", "rc", "editable"]
        if any(txt in version for txt in dev_versions) and not force:
            logger.info(f"skipping check for development version {version}")
            return
        req_version : str = self.yaml._get_path("version.kreate_version", None)
        if not req_version:
            logger.info(f"skipping check since no kreate_version specified")
            return
        # TODO: use more versatile semver check
        for v,r in zip(version.split("."), req_version.split(".")):
            if r != v and r != "*":
                raise ValueError(f"kreate version {version} does not match required version {req_version}")

    def dekrypt_bytes(b: bytes) -> bytes:
        raise NotImplementedError("dekrypt_bytes not implemented")
