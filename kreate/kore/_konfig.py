import os
import logging
import importlib
import base64
import pkg_resources
from jinja2 import filters
from pathlib import Path


from ._core import DeepChain, deep_update
from ._jinyaml import load_jinyaml, FileLocation


logger = logging.getLogger(__name__)


def b64encode(value: str) -> str:
    if value:
        res = base64.b64encode(value.encode("ascii"))
        return res.decode("ascii")
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
        self.values = {}
        self.functions = {"getenv": os.getenv}
        self.secrets = {}
        self._strukt_cache = None
        self._default_strukture_files = []
        self.dekrypt_func = None
        self._add_jinja_filter("b64encode", b64encode)
        self.yaml = load_jinyaml(
            FileLocation(self.filename, dir="."), {"function": self.functions}
        )
        deep_update(self.values, self.yaml.get("app", {}))
        self.appname = self.values["appname"]
        self.env = self.values["env"]
        self.target_dir = f"./build/{self.appname}-{self.env}"
        self.load()

    def _add_jinja_filter(self, name, func):
        filters.FILTERS[name] = func

    def load(self):
        self._load_files("values", self.values)
        self._load_files("secrets", self.secrets)

    def _load_files(self, key, dict_):
        logger.debug(f"loading {key} files")
        files = self.yaml.get(key, [])
        if not files:
            file = f"{key}-{self.appname}-{self.env}.yaml"
            if os.path.exists(f"{self.dir}/{file}"):
                logger.debug(f"adding standard {key} file {file}")
                files = [file]
            else:
                logger.info(f"no {key} files found")
        for fname in files:
            val_yaml = load_jinyaml(FileLocation(fname, dir=self.dir), dict_)
            if val_yaml:  # it can be empty
                deep_update(dict_, val_yaml)

    def _load_strukture_files(self):
        logger.debug("loading strukture files")
        result = []
        files = self._default_strukture_files
        files.extend(self.yaml.get("strukture", []))
        for fname in files:
            result.append(self._load_strukture_file(fname))
        return result

    def _load_strukture_file(self, filename):
        vars = {
            "konfig": self,
            "val": self.values,
            "var": self.values.get("vars",{}),
            "secret": self.secrets,
            "function": self.functions,
        }
        return load_jinyaml(FileLocation(filename, dir=self.dir), vars)

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
