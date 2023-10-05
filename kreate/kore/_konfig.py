import os
import logging
import pkg_resources
from pathlib import Path
from typing import List, Set

from ._core import deep_update, wrap
from ._repo import FileGetter
from ._jinyaml import JinYaml


logger = logging.getLogger(__name__)


class Konfig:
    def __init__(self, filename: str = None):
        filename = filename or "konfig.yaml"
        if os.path.isdir(filename):
            filename += "/konfig.yaml"
        self.filename = filename
        self.dekrypt_func = None
        self.jinyaml = JinYaml(self)
        self.dir = Path(os.path.dirname(filename))
        filename = os.path.basename(filename)
        self.file_getter = FileGetter(self, self.dir)
        self.yaml = wrap(self.jinyaml.render(filename, {}))
        self.load_all_inkludes()

    #def __iter__(self):
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
        result = {} #"konf": self, "appname": self.appname, "env": self.env}
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

    def load_inkludes(
        self, inkludes: List[str], already_inkluded: Set[str]
    ) -> int:
        count = 0
        for fname in inkludes:
            if fname == "STOP":
                logger.debug(f"inkluded {count} new files")
                logger.info(f"stopping inkluding any more files")
                return 0
            if fname not in already_inkluded:
                count += 1
                already_inkluded.add(fname)
                self.load_inklude(fname)
        logger.debug(f"inkluded {count} new files")
        return count

    def load_inklude(self, fname:str):
        logger.info(f"inkluding {fname}")
        context = self._jinja_context()
        val_yaml = self.jinyaml.render(fname, context)
        if val_yaml:  # it can be empty
            deep_update(self.yaml, val_yaml)

    def get_requires(self):
        reqs = []
        filename = f"{self.dir}/requirements.txt"
        if os.path.exists(filename):
            with open(filename) as f:
                for line in f.readlines():
                    reqs.append(line.strip())
        for pckg in self.yaml.get("requires", {}).keys():
            version = self.yaml["requires"][pckg]
            reqs.append(f"{pckg}{version}")
        return reqs

    def check_requires(self):
        error = False
        for line in self.get_requires():
            try:
                logger.info(f"checking requirement {line}")
                pkg_resources.require(line)
            except (
                pkg_resources.VersionConflict,
                pkg_resources.DistributionNotFound,
            ) as e:
                logger.warn(e)
                error = True
        return error

    def dekrypt_bytes(b: bytes) -> bytes:
        raise NotImplementedError("dekrypt_bytes not implemented")
