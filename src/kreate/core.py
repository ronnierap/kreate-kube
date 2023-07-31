import os
import jinja2
import pkgutil
from collections import UserDict, UserList
from collections.abc import Mapping, Sequence

from ruamel.yaml import YAML

class DictWrapper(UserDict):
    def __init__(self, dict):
        # do not copy the original dict as the normal UserDict does
        # but wrap the original so that updates go to the original
        # __setattr__ is used, because the data attribute does not exist yet
        super().__setattr__("data", dict)

    def __getattr__(self, attr):
        if attr not in self.data:
            # TODO: more informative error message
            raise AttributeError(f"could not find attribute {attr} in {self}")
        else:
            return wrap(self.data[attr])

    def __setattr__(self, attr, val):
        self.data[attr] = val


class ListWrapper(UserList):
    def __init__(self, seq) -> None:
        # do not copy the original list as the normal UserList does
        # but wrap the original so that updates go to the original
        self.data = seq

    def __getitem__(self, idx):
        # Wrap the returned value
        return wrap(self._seq[idx])

def wrap(obj):
    if isinstance(obj, Sequence) and not isinstance(obj, ListWrapper):
        return ListWrapper(obj)
    if isinstance(obj, Mapping) and not isinstance(obj, DictWrapper):
        return DictWrapper(obj)
    return obj


class DeepChain(Mapping):
    def __init__(self, *maps: Mapping):
        self._maps = maps

    def __getitem__(self, key):
        all_vals = tuple(m.get(key, None) for m in self._maps)
        vals = tuple(v for v in all_vals if v is not None)
        nrof_map_vals = sum(isinstance(v,Mapping) for v in vals)
        if nrof_map_vals>0:
            if nrof_map_vals < len(vals):
                raise AttributeError(f"key {key} is not mergeable into dictionary since not all values are maps {vals}")
            args=list(m for m in vals)
            return DeepChain(*args)
        if len(vals)>0:
            return vals[0]
        return None

    def __getattr__(self, attr):
        if attr not in self:
            # TODO: more informative error message
            raise AttributeError(f"DeepChain object does not have attribute {attr}")
        else:
            return self[attr]

    def get(self, attr, default):
        if attr in self:
            return self[attr]
        return super().get(attr, default)

    def keys(self):
        result = set()
        for m in self._maps:
            for k in m.keys():
                result.add(k)
        return result

    def __len__(self):
        return len(self.keys())

    def __iter__(self):
        return iter(self.keys())

    def __contains__(self, key):
        for m in self._maps:
            if key in m:
                return True
        return False

    def __repr__(self):
        return f"DeepChain({self._maps})"


parser = YAML()

def loadOptionalYaml(filename):
    if os.path.exists(filename):
        with open(filename) as f:
            return parser.load(f)
    else:
        print(f"WARN: skipping yaml file {filename}")
        return {}

class YamlBase:
    def __init__(self,
                 app,
                 name: str = None,
                 filename: str = None,
                 config = None,
                 template: str = None):
        self.app = app
        self.kind = type(self).__name__
        self.name = name or app.name + "-" + self.kind.lower()
        self.ignored = False
        self.filename = filename or self.name + ".yaml"
        self.template = template or self.kind + ".yaml"
        self.typename = str(type(self)).lower()[19:-2]    #.lstrip("<class 'kreate.app").rstrip("'>")
        if config:
            self.config = config
        else:
            if self.typename in app.config and name in app.config[self.typename]:
                #print(f"DEBUG using config {self.typename}.{name}")
                self.config = app.config[self.typename][name]
                #print(self.config)
            else:
                #print(f"DEBUG could not find config {typename}.{name}")
                self.config = {}
        if self.config.get("ignore", False):
            print(f"INFO: ignoring {self.typename}.{self.name}")
            self.ignored = True
        else:
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
            "cfg": self.config,
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
    return



class ConfigChain(DeepChain):
    def __init__(self, *args):
        maps = []
        for fname in args:
            if os.path.exists(fname):
                print(f"loading  config {fname}")
                with open(fname) as f:
                    m = parser.load(f)
                maps.append(m)
            else:
                print(f"WARN: skipping config file {fname}")
        DeepChain.__init__(self, *maps) #maps[0], maps[1])
