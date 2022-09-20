import os
import jinja2

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

    def add_annotation(self, name: str, val: str) -> None:
        self.annotations[name] = val

    def add_label(self, name: str, val: str) -> None:
        self.labels[name] = val

    def __file(self) -> str:
        return self.app.target_dir + "/" + self.name + ".yaml"

    def kreate_file(self, env: Environment, template: str) -> None:
        os.makedirs(self.app.target_dir, exist_ok=True)
        tmpl = jinja2.Template(
            self.template,
            undefined=jinja2.StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True)
        vars = {
            self.kind.lower(): self,
            "app": self.app,
            "env": env}
        tmpl.stream(vars).dump(self.__file())
        print(tmpl.render(vars))
