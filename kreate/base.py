import os
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
        self.labels = dict()
        self.annotations = dict()
        self.__yaml = YAML()
        self.yaml = self.__yaml.load(self.render())

    def add_annotation(self, name: str, val: str) -> None:
        self.annotations[name] = val

    def add_label(self, name: str, val: str) -> None:
        self.labels[name] = val

    def __file(self) -> str:
        return self.app.target_dir + "/" + self.name + ".yaml"

    def kreate(self) -> None:
        self.kreate_file()

    def kreate_file(self) -> None:
        print(self.render())

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
