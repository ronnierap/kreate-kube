import os
import shutil
import inspect
import logging
from collections.abc import Mapping
import importlib

from ._core import  DeepChain, DictWrapper
from ._krypt import dekrypt
from ._jinyaml import load_jinyaml

logger = logging.getLogger(__name__)

def get_package_data(ur: str):
    module = importlib.import_module('my_package.my_module')
    my_class = getattr(module, 'MyClass')

def get_class(name: str):
    module_name = name.rsplit(".", 1)[0]
    class_name = name.rsplit(".", 1)[1]
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


class AppDef():
    def __init__(self, env, filename="appdef.yaml", *args):
        self.dir = os.path.dirname(filename)
        self.filename = filename
        self.env = env
        self.values = { "env": env, "dekrypt": dekrypt, "getenv": os.getenv }
        self.yaml = load_jinyaml(filename, self.values)
        self.values.update(self.yaml.get("values",{}))
        self.app_class = get_class(self.yaml.get("app_class","kreate.KustApp"))

        for fname in self.yaml.get("value_files",[]):
            val_yaml = load_jinyaml(fname, self.values, dirname=self.dir)
            self.values.update(val_yaml)

        self.konfig_dicts = []
        for fname in self.yaml.get("konfig_files"):
            self.add_konfig_file(fname, dirname=self.dir)
        #self.add_konfig_file(f"@kreate.templates:default-values.yaml")#, package=templates )

    def add_konfig_file(self, filename, package=None, dirname=None):
        vars = { "val": self.values }
        yaml = load_jinyaml(filename, vars, package=package, dirname=dirname)
        self.konfig_dicts.append(yaml)

    def konfig(self):
        return DeepChain(*reversed(self.konfig_dicts))

    def kreate_app(self):
        app: App = self.app_class(self)
        for key in self.yaml.get("templates",[]):
            templ = self.yaml['templates'][key]
            logger.info(f"adding custom template {key}: {templ}")
            app.register_template_file(key, templ)
        return app


class App():
    def __init__(self, appdef: AppDef):
        self.name = appdef.values["app"]
        self.env = appdef.env
        self.appdef = appdef
        self.konfig = appdef.konfig()
        self.values = appdef.values
        self.namespace = self.name + "-" + self.env
        self.target_dir = "./build/" + self.namespace
        self.templates = {}
        self.komponents = []
        self._kinds = {}
        self.aliases = {}
        self.register_std_templates()
        self._init()

    def _init(self):
        pass

    def register_template(self, name: str, template, aliases=None):
        if name in self.templates:
            logger.warning(f"overriding template {name}")
        logger.debug(f"registering template {name}: {template}")
        self.templates[name] = template
        if aliases:
            self.add_alias(name, aliases)

    def register_template_class(self, cls, aliases=None):
        # TODO: determine package more smart
        # f"py:kreate.templates:{cls.__name__}.yaml"
        self.register_template(cls.__name__, cls, aliases=aliases)

    def register_template_file(self, name, filename=None, aliases=None):
        filename = filename or f"py:kreate.templates:{name}.yaml"
        self.register_template(name, filename, aliases=aliases)

    def register_std_templates(self) -> None:
        pass

    def add_alias(self, kind: str, *aliases: str ) -> None:
        if kind in self.aliases:
            self.aliases[kind].append(aliases)
        else:
            self.aliases[kind] = list(aliases)

    def get_aliases(self, kind: str):
        result = [kind, kind.lower()]
        if kind in self.aliases:
            result.append(*self.aliases[kind])
        return result

    def add(self, res) -> None:
        if not res.skip:
            self.komponents.append(res)
        map = self._kinds.get(res.kind, None)
        if map is None:
            map = DictWrapper({})
            self.get_aliases(res.kind)
            for alias in self.get_aliases(res.kind):
                self._kinds[alias] = map

        map[res.shortname] = res

    def __getattr__(self, attr):
        if attr in self.__dict__ or attr == "_dict":
            return super().__getattribute__(attr)
        return self._kinds.get(attr, None)

    def kreate_komponent(self, kind: str, shortname: str = None, **kwargs):
        templ = self.templates[kind]
        if inspect.isclass(templ):
            return templ(self, shortname=shortname, kind=kind, **kwargs)
        else:
            raise ValueError(f"Unknown template type {type(templ)}, {templ}")

    def kreate_files(self):
        if os.path.exists(self.target_dir) and os.path.isdir(self.target_dir):
            shutil.rmtree(self.target_dir)
        os.makedirs(self.target_dir, exist_ok=True)

        for obj  in self.komponents:
            if (obj.filename):
                logger.info(f"kreating file {obj.filename}")
                obj.kreate_file()
            else:
                logger.info(f"skipping file for {obj.kind}.{obj.shortname}")


    def _shortnames(self, kind:str ) -> list:
        if kind in self.konfig:
            return self.konfig[kind].keys()
        return []

    def konfigure_from_konfig(self):
        for kind in sorted(self.konfig.keys()):
            if kind in self.templates:
                for shortname in sorted(self.konfig[kind].keys()):
                    logger.info(f"konfiguring {kind}.{shortname}")
                    self.kreate_komponent(kind, shortname)
            elif kind != "default":
                logger.warning(f"Unknown toplevel komponent {kind}")
