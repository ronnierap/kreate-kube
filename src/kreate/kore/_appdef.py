import os
import logging
import importlib
import base64

from ._core import DeepChain
from ._jinyaml import load_jinyaml, FileLocation
import jinja2.filters


logger = logging.getLogger(__name__)


def b64encode(value: str) -> str:
    if value:
        res = base64.b64encode(value.encode("ascii"))
        return res.decode("ascii")
    print("empty")
    return ""


jinja2.filters.FILTERS["b64encode"] = b64encode


def get_class(name: str):
    module_name = name.rsplit(".", 1)[0]
    class_name = name.rsplit(".", 1)[1]
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


class AppDef():
    def __init__(self, filename="appdef.yaml", *args):
        if os.path.isdir(filename):
            filename += "/appdef.yaml"
        self.dir = os.path.dirname(filename)
        self.filename = filename
        self.values = {"getenv": os.getenv}
        self.yaml = load_jinyaml(FileLocation(filename, dir="."), self.values)
        self.values.update(self.yaml.get("values", {}))
        self.name = self.values["app"]
        self.env = self.values["env"]

    def _load_strukture_files(self, pre_files=None, post_files=None):
        for fname in self.yaml.get("value_files", []):
            val_yaml = load_jinyaml(FileLocation(
                fname, dir=self.dir), self.values)
            self.values.update(val_yaml)
        result = []
        files = pre_files or []
        files.extend(self.yaml.get("strukture_files",[]))
        files.extend(post_files or [])
        for fname in files:
            result.append(self._load_strukture_file(fname))
        return result

    def _load_strukture_file(self, filename):
        vars = {"val": self.values}
        return load_jinyaml(FileLocation(filename, dir=self.dir), vars)

    def calc_strukture(self, pre_files=None, post_files=None):
        dicts = self._load_strukture_files(pre_files=pre_files, post_files=post_files)
        return DeepChain(*reversed(dicts))
