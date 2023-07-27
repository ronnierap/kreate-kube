import os
import jinja2
import pkgutil

from ruamel.yaml import YAML
from .wrapper import wrap

parser = YAML()

def loadOptionalYaml(filename):
    if os.path.exists(filename):
        with open(filename) as f:
            return parser.load(f)
    else:
        return {}

class YamlBase:
    def __init__(self,
                 app,
                 name: str = None,
                 filename: str = None,
                 template: str = None):
        self.app = app
        self.kind = type(self).__name__
        self.name = name or app.name + "-" + self.kind.lower()
        self.filename = filename or self.name + ".yaml"
        self.template = template or self.kind + ".yaml"

        _parsed = parser.load(self.render())
        self.yaml = wrap(_parsed)

    def kreate(self) -> None:
        print("kreating "+self.filename)
        with open(self.app.target_dir + "/" + self.filename, 'wb') as f:
            #pprint.pprint(self.yaml.data)
            parser.dump(self.yaml.data, f)

    def annotate(self, name: str, val: str) -> None:
        if "annotations" not in self.yaml.metadata:
            self.yaml.metadata["annotations"]={}
        self.yaml.metadata.annotations[name]=val

    def add_label(self, name: str, val: str) -> None:
        if "labels" not in self.yaml.metadata:
            self.yaml.metadata["labels"]={}
        self.yaml.metadata.labels[name]=val

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
            "config": self.app.config,
            "my": self,
        }
        self._add_jinja_vars(vars)
        if outfile:
            tmpl.stream(vars).dump(outfile)
        else:
            return tmpl.render(vars)

    def _add_jinja_vars(self, vars):
        pass




def merge(a, b, path=None):
    "merges b into a"
    if path is None: path = []
    for key in b:
        valb = b[key]
        if key in a:
            vala=a[key]
            if isinstance(vala, dict) and isinstance(valb, dict):
                merge(vala, valb, path + [str(key)])
            elif a[key] == valb:
                pass # same leaf value
            else:
                a[key] = valb
                print('overriding %s' % '.'.join(path + [str(key)]))
        else:
            a[key] = valb
    return a

## see: https://towardsdatascience.com/what-is-lazy-evaluation-in-python-9efb1d3bfed0
#def lazy_property(fn):
#    attr_name = '_lazy_' + fn.__name__
#
#    @property
#    def _lazy_property(self):
#        if not hasattr(self, attr_name):
#            setattr(self, attr_name, fn(self))
#        return getattr(self, attr_name)
#    return _lazy_property
#    @lazy_property
#    def yaml(self):
#        # Only parse yaml when needed
#        #print("yaml property is parsed for "+self.name)
#        self._parsed = self.__yaml.load(self.render())
#        return DictWrapper(self._parsed)
