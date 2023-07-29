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
            raise AttributeError(f"Yaml object does not have attribute {attr}")
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
    def __init__(self, map: Mapping, parent: Mapping):
        self._parent = parent
        self._map = map

    def __getitem__(self, key):
        val = self._map.get(key, None)
        pval = self._parent.get(key, None)
        if isinstance(val,Mapping) and isinstance(pval,Mapping):
            return DeepChain(val, pval)
        if isinstance(val,Mapping) or isinstance(pval,Mapping):
            raise AttributeError(f"key {key} is not mergeable for {type(val)} and {type(pval)}")
        return self._map.get(key, pval) # TODO will return None instead of attribute error

    def __getattr__(self, attr):
        if attr not in self:
            # TODO: more informative error message
            raise AttributeError(f"DeepChain object does not have attribute {attr}")
        else:
            return wrap(self[attr])

    def __len__(self):
        keys = { **self._map, **self._parent }
        return len(keys)

    def __iter__(self): # chain_from_iterable=chain.from_iterable
        keys = { **self._map, **self._parent }
        return iter(keys)

    def __contains__(self, key):
        if key in self._map:
            return True
        return key in self._parent

    def __repr__(self):
        return f"DeepChain({self._map},{self._parent})"


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
