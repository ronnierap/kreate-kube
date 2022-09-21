import os
import sys
import jinja2
import pkgutil
from collections import OrderedDict

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

from .app import App

class Base:
    def __init__(self,  app: App, kind: str, clz,
                 name: str = None, subname: str = ""):
        if name is None:
            self.name = app.name + "-" + kind.lower() + subname
        else:
            self.name = name
        self.app = app
        self.kind = kind
        self.__yaml = YAML()
        self.yaml = DictWrapper(self.__yaml.load(self.render()))

    def annotate(self, name: str, val: str) -> None:
        self.yaml.metadata.annotations.add(name,val)

    def add_label(self, name: str, val: str) -> None:
        self.yaml.labels.add(name, val)

    def __file(self) -> str:
        return self.app.target_dir + "/" + self.name + ".yaml"

    def kreate(self) -> None:
        os.makedirs(self.app.target_dir, exist_ok=True)
        self.__yaml.dump(self.yaml._dict, sys.stdout)

    def render(self) -> None:
        filename = self.kind.lower() + ".yaml"
        template = pkgutil.get_data(__package__, filename).decode('utf-8')
        tmpl = jinja2.Template(
            template,
            undefined=jinja2.StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True)
        vars = {
            "this": self,  # TODO: better name, self is already used by jinja
            self.kind.lower(): self,
            "app": self.app,
            "env": self.app.env}
        tmpl.stream(vars).dump(self.__file())
        return tmpl.render(vars)


class DictWrapper():
    def __init__(self, somedict) -> None:
        self._dict = somedict

    def __getattr__(self, attr):
        if attr in self.__dict__ or attr=="_dict":
            return super().__getattribute__(attr)
        result = self._dict[attr]
        if isinstance(result, dict):
            return DictWrapper(result)
        return result

    def add(self, key, value):
        self._dict[key]=value

    def __setattr__(self, attr, val):
        if attr in self.__dict__ or attr=="_dict":
            return super().__setattr__(attr, val)
        self._dict[attr]=val
