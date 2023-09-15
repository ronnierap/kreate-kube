import os
import logging
import importlib
import base64
import pkg_resources
from jinja2 import filters
from pathlib import Path
from typing import List, Set

from ._core import DeepChain, deep_update
from ._repo import FileGetter
from ._jinyaml import render_jinyaml, FileLocation


logger = logging.getLogger(__name__)


def b64encode(value: str) -> str:
    if value:
        if isinstance(value, bytes):
            res = base64.b64encode(value)
        else:
            res = base64.b64encode(value.encode())
        return res.decode()
    else:
        logger.warning("empty value to b64encode")
        return ""


def get_class(name: str):
    module_name = name.rsplit(".", 1)[0]
    class_name = name.rsplit(".", 1)[1]
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


class Konfig:
    def __init__(self, filename: str = None):
        filename = filename or "konfig.yaml"
        if os.path.isdir(filename):
            filename += "/konfig.yaml"
        self.dir = os.path.dirname(filename) or "."
        self.filename = filename
        #self.functions = {"getenv": os.getenv}
        self._strukt_cache = None
        self._default_strukture_files = []
        self.dekrypt_func = None
        self._add_jinja_filter("b64encode", b64encode)
        self.file_getter = FileGetter(self)
        data = self.file_getter.get_data(self.filename, ".")
        self.yaml = render_jinyaml(data, {}) #{"function": self.functions})
        self.appname = self.yaml["appname"]
        self.env = self.yaml["env"]
        self.target_dir = f"./build/{self.appname}-{self.env}"
        self.target_path = Path(self.target_dir)
        self.load()

    def __getattr__(self, attr):
        if attr not in self.yaml:
            raise AttributeError(f"could not find attribute {attr} in {self}")
        else:
            return self.yaml[attr]

    def _jinja_context(self):
        result = {"konf": self, "appname": self.appname, "env": self.env}
        for k in self.yaml.keys():
            v = self.yaml[k]
            result[k] = v
        return result

    def _add_jinja_filter(self, name, func):
        filters.FILTERS[name] = func

    def load_data(self, fname:str) -> str:
        return self.file_getter.get_data(fname, dir=self.dir)

    def load(self):
        self.load_all_inkludes()

    def load_all_inkludes(self):
        logger.debug("loading inklude files")
        already_inkluded = set()
        inkludes = self.yaml.get("inklude", [])
        # keep loading inkludes until all is done
        while self.load_inkludes(inkludes, already_inkluded) > 0:
            # possible new inkludes are added
            inkludes = self.yaml.get("inklude", [])

    def load_inkludes(self,
        inkludes: List[str],
        already_inkluded: Set[str]
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
                logger.info(f"inkluding {fname}")
                # TODO: use dirname
                data = self.load_data(fname)
                val_yaml = render_jinyaml(data, self._jinja_context() )
                if val_yaml:  # it can be empty
                    deep_update(self.yaml, val_yaml)
        logger.debug(f"inkluded {count} new files")
        return count

    def _load_strukture_files(self):
        logger.debug("loading strukture files")
        result = []
        files = self._default_strukture_files
        files.extend(self.yaml.get("strukture", []))
        for fname in files:
            result.append(self._load_strukture_file(fname))
        return result

    def _load_strukture_file(self, filename):
        data = self.file_getter.get_data(filename, self.dir)
        return render_jinyaml(data, self.yaml)  # TODO: dir=self.dir

    def calc_strukture(self):
        if not self._strukt_cache:
            dicts = self._load_strukture_files()
            self._strukt_cache = DeepChain(*reversed(dicts))
        return self._strukt_cache

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
