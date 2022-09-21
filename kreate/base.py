import os
import sys
import jinja2
import pkgutil

from ruamel.yaml import YAML

from .app import App
from .environment import Environment


class Base:
    def __init__(self, app: App, kind: str,
                 name: str = None, subname: str = ""):
        if name is None:
            self.name = app.name + "-" + kind.lower() + subname
        else:
            self.name = name
        self.app = app
        self.kind = kind
        self.__yaml = YAML()
        self.yaml = self.__yaml.load(self.render())

    def annotate(self, name: str, val: str) -> None:
        self.yaml["metadata"]["annotations"][name] = val

    def add_label(self, name: str, val: str) -> None:
        self.yaml.labels[name] = val

    def __file(self) -> str:
        return self.app.target_dir + "/" + self.name + ".yaml"

    def kreate(self) -> None:
        os.makedirs(self.app.target_dir, exist_ok=True)
        self.__yaml.dump(self.yaml, sys.stdout)

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
