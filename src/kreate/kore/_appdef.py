import os
import logging
import importlib
import base64

from ._core import DeepChain
from ._jinyaml import load_jinyaml, FileLocation


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


class AppDef():
    def __init__(self, filename="appdef.yaml", *args):
        if os.path.isdir(filename):
            filename += "/appdef.yaml"
        self.dir = os.path.dirname(filename) or "."
        self.filename = filename
        self.values = {"getenv": os.getenv}
        self.yaml = load_jinyaml(FileLocation(filename, dir="."), self.values)
        self.values.update(self.yaml.get("values", {}))
        self.appname = self.values["appname"]
        self.env = self.values["env"]
        self._strukt_cache = None
        self._load_value_files()
        self._default_strukture_files = []

    def _load_value_files(self):
        logger.debug("loading value files")
        for fname in self.yaml.get("value_files", []):
            val_yaml = load_jinyaml(FileLocation(
                fname, dir=self.dir), self.values)
            self.values.update(val_yaml)

    def _load_strukture_files(self):
        logger.debug("loading strukture files")
        result = []
        files = self._default_strukture_files
        files.extend(self.yaml.get("strukture_files", []))
        #files.extend(post_files or [])
        for fname in files:
            result.append(self._load_strukture_file(fname))
        return result

    def _load_strukture_file(self, filename):
        vars = {"val": self.values, "appdef": self}
        return load_jinyaml(FileLocation(filename, dir=self.dir), vars)

    def calc_strukture(self):
        if not self._strukt_cache:
            dicts = self._load_strukture_files()
            self._strukt_cache = DeepChain(*reversed(dicts))
        return self._strukt_cache
