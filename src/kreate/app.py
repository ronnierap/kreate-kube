import os
import sys
import shutil
import logging
from collections.abc import Mapping
import importlib


from . import core, jinyaml, templates

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
        self.kreate_app_func = None
        self.values = { "env": env }
        yaml = jinyaml.load_jinyaml(filename, self.values)
        self.values.update(yaml.get("values",{}))
        self.app_class = get_class(yaml.get("app_class","kreate.KustApp"))

        for fname in yaml.get("value_files",[]):
            val_yaml = jinyaml.load_jinyaml(fname, self.values, dirname=self.dir)
            self.values.update(val_yaml)

        self.maps = []
        for fname in yaml.get("config_files"):
            self.add_config_file(fname, dirname=self.dir)
        #self.add_config_file(f"@kreate.templates:default-values.yaml")#, package=templates )

    def add_config_file(self, filename, package=None, dirname=None):
        vars = { "val": self.values }
        yaml = jinyaml.load_jinyaml(filename, vars, package=package, dirname=dirname)
        self.maps.append(yaml)

    def config(self):
        return core.DeepChain(*self.maps)

    def kreate_app(self):
        app = App(self)
        if self.kreate_app_func:
            app = self.kreate_app_func(appdef=self)
        else:
            app = self.app_class(self)
            app.kreate_from_config()
        return app


class App():
    def __init__(self, appdef: AppDef):
        self.name = appdef.values["app"]
        self.env = appdef.env
        self.appdef = appdef
        self.script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.vars = dict()
        self.config = appdef.config()
        self.values = appdef.values
        self.namespace = self.name + "-" + self.env
        self.target_dir = "./build/" + self.namespace
        self.komponents = []
        self._kinds = {}
        self.aliases = {}
        self.add_std_aliases()
        self._init()

    def _init(self):
        pass

    def add_std_aliases(self) -> None:
        self.add_alias("Service", "svc")
        self.add_alias("Deployment", "depl")
        self.add_alias("PodDisruptionBudget", "pdb")
        self.add_alias("ConfigMap", "cm")
        self.add_alias("HorizontalPodAutoscaler", "hpa")


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
            map = core.DictWrapper({})
            self.get_aliases(res.kind)
            for alias in self.get_aliases(res.kind):
                self._kinds[alias] = map

        map[res.shortname] = res

    def __getattr__(self, attr):
        if attr in self.__dict__ or attr == "_dict":
            return super().__getattribute__(attr)
        return self._kinds.get(attr, None)

    def kreate_resource(self, kind: str, shortname: str = None, **kwargs):
        return Resource(self, shortname=shortname, kind=kind, **kwargs)

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
        if kind in self.config:
            return self.config[kind].keys()
        return []


    def kreate_from_config(self):
        for shortname in self._shortnames("Egress"):
            Egress(self, shortname)
        for shortname in self._shortnames("Ingress"):
            Ingress(self, shortname)
        for shortname in self._shortnames("Deployment"):
            Deployment(self, shortname)
        for shortname in self._shortnames("Service"):
            Service(self, shortname)
        for shortname in self._shortnames("PodDisruptionBudget"):
            PodDisruptionBudget(self, shortname)
        for shortname in self._shortnames("ConfigMap"):
            ConfigMap(self, shortname)
        for kind in ("ServiceAccount", "ServiceMonitor", "HorizontalPodAutoscaler"):
            for shortname in self._shortnames(kind):
                self.kreate_resource(kind, shortname)


##################################################################

class Komponent(core.YamlBase):
    """An object that is parsed from a yaml template and configuration"""
    def __init__(self, app: App,
                 shortname: str = None,
                 kind: str = None,
                 template: str = None,
                 **kwargs
                 ):
        self.app = app
        self.kind = kind or self.__class__.__name__
        self.shortname = shortname or "main"
        self.config = self._calc_config(kwargs)

        template = template or f"{self.kind}.yaml"
        core.YamlBase.__init__(self, template)
        self._init()
        self.skip = self.config.get("ignore", False)
        self.name = self.config.get("name", None) or self.calc_name().lower()
        if self.skip:
            # do not load the template (config might be missing)
            logger.info(f"ignoring {self.name}")
        else:
            self.load_yaml()
        self.app.add(self)
        self.invoke_options()

    # to prevent subclass to make own constructors
    def _init(self):
        pass

    def calc_name(self):
        if self.shortname == "main":
            return f"{self.app.name}-{self.kind}"
        return f"{self.app.name}-{self.kind}-{self.shortname}"

    def _calc_config(self, extra):
        cfg = self._find_config()
        defaults = self._find_defaults()
        return core.DeepChain(extra, cfg, {"default": defaults})

    def _find_defaults(self):
        if self.kind in self.app.config.default:
            logger.debug(f"using defaults for {self.kind}")
            return self.app.config.default[self.kind]
        return {}

    def _find_config(self):
        typename = self.kind
        if typename in self.app.config and self.shortname in self.app.config[typename]:
            logger.debug(f"using named config {typename}.{self.shortname}")
            return  self.app.config[typename][self.shortname]
        logger.info(f"could not find config for {typename}.{self.shortname} in")
        return {}

    def kreate_file(self) -> None:
        filename = self.filename
        if filename:
            dir = self.dirname
            self.save_yaml(f"{dir}/{filename}")

    def _template_vars(self):
        return {
            "cfg" : self.config,
            "default" : self.config.default,
            "app" : self.app,
            "my" : self,
            "val": self.app.values
        }

    def invoke_options(self):
        options = self.config.get("options", [])
        for opt in options:
            if type(opt) == str:
                logger.debug(f"invoking {self.name} option {opt}")
                getattr(self, opt)()
            elif isinstance(opt, Mapping):
                for key in opt.keys():
                    val = opt.get(key)
                    if isinstance(val, Mapping):
                        logger.debug(f"invoking {self.name} option {key} with kwargs parameters {val}")
                        getattr(self, key)(**dict(val))
                    if isinstance(val, list):
                        logger.debug(f"invoking {self.name} option {key} with list parameters {val}")
                        getattr(self, key)(*val)
                    elif isinstance(val, str):
                        logger.debug(f"invoking {self.name} option {key} with string parameter {val}")
                        getattr(self, key)(val)
                    elif isinstance(val, int):
                        logger.debug(f"invoking {self.name} option {key} with int parameter {val}")
                        getattr(self, key)(int(val))
                    else:
                        logger.warn(f"option map {opt} for {self.name} not supported")

            else:
                logger.warn(f"option {opt} for {self.name} not supported")


    @property
    def dirname(self):
        return self.app.target_dir

    @property
    def filename(self):
        return f"{self.kind.lower()}-{self.shortname}.yaml"


class Resource(Komponent):
    def __init__(self,
                 app: App,
                 shortname: str = None,
                 kind: str = None,
                 template: str = None,
                 **kwargs
                ):
        Komponent.__init__(self, app, kind=kind, shortname=shortname, template=template, **kwargs)
        self.add_metadata()


    @property
    def filename(self):
        # prefix the file, because the name of a resource is not guaranteed
        # to be unique
        return f"{self.kind}-{self.name}.yaml".lower()

    def add_metadata(self):
        for key in self.config.get("annotations", {}):
            if not "annotations" in self.yaml.metadata:
                self.yaml.metadata.annotations={}
            self.yaml.metadata.annotations[key]=self.config.annotations[key]
        for key in self.config.get("labels", {}):
            if not "labels" in self.yaml.metadata:
                self.yaml.metadata.labels={}
            self.yaml.metadata.labels[key]=self.config.labels[key]


    def annotation(self, name: str, val: str) -> None:
        if "annotations" not in self.yaml.metadata:
            self.yaml.metadata["annotations"]={}
        self.yaml.metadata.annotations[name]=val

    def label(self, name: str, val: str) -> None:
        if "labels" not in self.yaml.metadata:
            self.yaml.metadata["labels"]={}
        self.yaml.metadata.labels[name]=val

class Deployment(Resource):
    def calc_name(self):
        if  self.shortname == "main":
            return self.app.name
        return f"{self.app.name}-{self.shortname}"

    def pod_annotation(self, name: str, val: str) -> None:
        if not "annotations" in self.yaml.spec.template.metadata:
            self.yaml.spec.template.metadata["annotations"] = {}
        self.yaml.spec.template.metadata.annotations[name] = val

    def pod_label(self, name: str, val: str) -> None:
        if not "labels" in self.yaml.spec.template.metadata:
            self.yaml.spec.template.metadata["labels"] = {}
        self.yaml.spec.template.metadata.labels[name] = val


class PodDisruptionBudget(Resource):
    pass

class Service(Resource):
    def headless(self):
        self.yaml.spec.clusterIP="None"

class Egress(Resource):
    def calc_name(self):
        return f"{self.app.name}-egress-to-{self.shortname}"



class ConfigMap(Resource):
    def calc_name(self):
        return f"{self.app.name}-{self.shortname}"

    @property
    def filename(self) -> str:
        return super().filename

    def add_var(self, name, value=None):
        if value is None:
            value = self.app.values[name]
        # We can not use self.yaml.data, since data is a field in UserDict
        self.yaml["data"][name] = value


class Ingress(Resource):
    def nginx_annon(self, name: str, val: str) -> None:
        self.annotation("nginx.ingress.kubernetes.io/" + name, val)

    def sticky(self) -> None:
        self.nginx_annon("affinity", "cookie")

    def rewrite_url(self, url: str) -> None:
        self.nginx_annon("rewrite-target", url)

    def read_timeout(self, sec: int) -> None:
        self.nginx_annon("proxy-read-timeout", str(sec))

    def max_body_size(self, size: int) -> None:
        self.nginx_annon("proxy-body-size", str(size))

    def whitelist(self, whitelist: str) -> None:
        self.nginx_annon("whitelist-source-range", whitelist)

    def session_cookie_samesite(self) -> None:
        self.nginx_annon("session-cookie-samesite", "None")

    def basic_auth(self, secret: str = "basic-auth") -> None:
        self.nginx_annon("auth-type", "basic")
        self.nginx_annon("auth-secret", secret)
        self.nginx_annon("auth-realm", self.app.name + "-realm")
