import os
import logging
import importlib
import base64
from jinja2 import filters

from ._core import DeepChain
from ._jinyaml import load_jinyaml, load_data, load_jinja_data, FileLocation


logger = logging.getLogger(__name__)


def b64encode(value: str) -> str:
    if value:
        res = base64.b64encode(value.encode("ascii"))
        return res.decode("ascii")
    print("empty")
    return ""


def get_class(name: str):
    module_name = name.rsplit(".", 1)[0]
    class_name = name.rsplit(".", 1)[1]
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


class Konfig():
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
        self._add_jinja_filter("b64encode",  b64encode)
        self.yaml = load_jinyaml(FileLocation(self.filename, dir="."), {"function": self.functions})
        self.values.update(self.yaml.get("values", {}).get("vars", {}))
        self.appname = self.values["appname"]
        self.env = self.values["env"]
        self.target_dir = f"./build/{self.appname}-{self.env}"

        self.load()

    def _add_jinja_filter(self, name, func):
        filters.FILTERS[name] = func


    def load(self):
        self._load_files("values", self.values)
        self._load_files("secrets", self.secrets)
        self.kopy_files("files", "files")
        self.kopy_files("secret_files", "secrets/files", dekrypt_default=True)

    def _load_files(self, key, dict_):
        logger.debug(f"loading {key} files")
        files = self.yaml.get(key, {}).get("files", [])
        if not files:
            file = f"{key}-{self.appname}-{self.env}.yaml"
            if os.path.exists(f"{self.dir}/{file}"):
                logger.debug(f"adding standard {key} file {file}")
                files = [file]
            else:
                logger.info(f"no {key} files found")

        for fname in files:
            val_yaml = load_jinyaml(FileLocation(fname, dir=self.dir), dict_)
            dict_.update(val_yaml)

    def _load_strukture_files(self):
        logger.debug("loading strukture files")
        result = []
        files = self._default_strukture_files
        files.extend(self.yaml.get("strukture", []))
        #files.extend(post_files or [])
        for fname in files:
            result.append(self._load_strukture_file(fname))
        return result

    def _load_strukture_file(self, filename):
        vars = {
                "konfig": self,
                "val": self.values,
                "secret": self.secrets,
                "function": self.functions,
        }
        return load_jinyaml(FileLocation(filename, dir=self.dir), vars)

    def calc_strukture(self):
        if not self._strukt_cache:
            dicts = self._load_strukture_files()
            self._strukt_cache = DeepChain(*reversed(dicts))
        return self._strukt_cache

    def kopy_files(self, key, target_subdir, dekrypt_default=False ):
        file_list = self.yaml.get(key, [])
        if not file_list:
            return
        os.makedirs(f"{self.target_dir}/{target_subdir}", exist_ok=True)
        for file in file_list:
            dekrypt = file.get("dekrypt", dekrypt_default)
            name = file.get("name", None)
            if not name:
                raise ValueError(f"file in konfig {key} should have name {file}")
            from_ = file.get("from", f"{key}/{name}" +(".encrypted" if dekrypt else f""))
            template = file.get("template", False)
            loc = FileLocation(from_, dir=self.dir)
            if template:
                vars = {
                        "konfig": self,
                        "val": self.values,
                        "secret": self.secrets,
                }
                logger.info(f"rendering template {from_} to {key}/{name}")
                data = load_jinja_data(loc, vars)
            else:
                logger.info(f"kopying {from_} to {key}/{name}")
                data = load_data(loc)
            if dekrypt:
                data = "TODO: dekrypt from other module"
            with open(f"{self.target_dir}/{target_subdir}/{name}", "w") as f:
                f.write(data)
