import sys
import jinja2
import pkgutil

from ruamel.yaml import YAML

from .app import App
from .wrapper import DictWrapper


class Base:
    def __init__(self,
                 app: App,
                 name: str = None,
                 filename: str = None,
                 template: str = None):
        self.app = app
        self.app.resources.append(self)
        self.kind = type(self).__name__
        self.name = name or app.name + "-" + self.kind.lower()
        self.filename = filename or self.name + ".yaml"
        self.template = template or self.kind + ".yaml"
        self.annotations = {}
        self.labels = {}
        self.__yaml = YAML()
        self.__parsed = self.__yaml.load(self.render())
        self.yaml = DictWrapper(self.__parsed)

    def kreate(self) -> None:
        print(self.filename)
        with open(self.app.target_dir + "/" + self.filename, 'wb') as f:
            self.__yaml.dump(self.__parsed, f)

    def dump(self) -> None:
        self.__yaml.dump(self.yaml._dict, sys.stdout)

    def annotate(self, name: str, val: str) -> None:
        self.annotations[name] = val

    def add_label(self, name: str, val: str) -> None:
        self.labels.add[name] = val

    def render(self, outfile=None):
        template_data = pkgutil.get_data(self.app.template_package.__package__,
                                         self.template).decode('utf-8')
        tmpl = jinja2.Template(
            template_data,
            undefined=jinja2.StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True)
        vars = {
            "app": self.app,
            "vars": self.app.vars,
            self.kind.lower(): self}
        if outfile:
            tmpl.stream(vars).dump(outfile)
        else:
            return tmpl.render(vars)
