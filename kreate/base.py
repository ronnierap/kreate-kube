import sys
import jinja2
import pkgutil

from ruamel.yaml import YAML

from .app import App
from .wrapper import DictWrapper

# see: https://towardsdatascience.com/what-is-lazy-evaluation-in-python-9efb1d3bfed0
def lazy_property(fn):
    attr_name = '_lazy_' + fn.__name__

    @property
    def _lazy_property(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)
    return _lazy_property



class Base:
    def __init__(self,
                 app: App,
                 name: str = None,
                 filename: str = None,
                 template: str = None):
        self.app = app
        self.kind = type(self).__name__
        self.name = name or app.name + "-" + self.kind.lower()
        self.filename = filename or self.name + ".yaml"
        self.template = template or self.kind + ".yaml"
        self.__yaml = YAML()

    @lazy_property
    def yaml(self):
        # Only parse yaml when needed
        #print("yaml property is parsed for "+self.name)
        self.__parsed = self.__yaml.load(self.render())
        return DictWrapper(self.__parsed)

    def kreate(self) -> None:
        print(self.filename)
        with open(self.app.target_dir + "/" + self.filename, 'wb') as f:
            self.__yaml.dump(self.__parsed, f)

    def dump(self) -> None:
        self.__yaml.dump(self.yaml._dict, sys.stdout)

    def annotate(self, name: str, val: str) -> None:
        if not self.yaml.metadata.has_key("annotations"):
            self.yaml.metadata.add("annotations", {})
        self.yaml.metadata.annotations.add(name, val)

    def add_label(self, name: str, val: str) -> None:
        if not self.yaml.metadata.has_key("labels"):
            self.yaml.metadata.add("labels", {})
        self.yaml.metadata.labels.add(name, val)

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
            "my": self,
        }
        if outfile:
            tmpl.stream(vars).dump(outfile)
        else:
            return tmpl.render(vars)
