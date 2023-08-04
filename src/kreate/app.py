import os
import sys
import shutil
import logging
from collections.abc import Mapping

from . import core

logger = logging.getLogger(__name__)

class App():
    def __init__(
            self,
            config: core.AppConfig,
            env: str,
        ):
        self.name = config.values["app"]
        self.script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.vars = dict()
        self.config = config.config()
        self.values = config.values
        self.env = env
        self.namespace = self.name + "-" + self.env
        self.target_dir = "./build/" + self.namespace
        self.yaml_objects = []
        self._kinds = {}
        self.aliases = {}
        self.add_std_aliases()

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
            self.yaml_objects.append(res)
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

        for obj  in self.yaml_objects:
            obj.kreate_file()
        if self.need_kustomize():
            kust = Kustomization(self)
            kust.kreate_file()

    def need_kustomize(self):
        for res in self.yaml_objects:
            if res.need_kustomize():
                return True
        return False

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
        for res in self.yaml_objects:
            if isinstance(res, Resource): # should always be?
                res.add_patches()



##################################################################

class YamlObject(core.YamlBase):
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
        self.config = self._find_config(kwargs)
        template = template or f"{self.kind}.yaml"
        core.YamlBase.__init__(self, template)
        self.skip = self.config.get("ignore", False)
        self.name = self.config.get("name", None) or self.calc_name().lower()
        if self.skip:
            # do not load the template (config might be missing)
            logger.info(f"ignoring {self.name}")
        else:
            self.load_yaml()
        self.app.add(self)
        self.invoke_options()

    def calc_name(self):
        if self.shortname == "main":
            return f"{self.app.name}-{self.kind}"
        return f"{self.app.name}-{self.kind}-{self.shortname}"


    def _find_config(self, extra):
        typename = self.kind
        if typename in self.app.config and self.shortname in self.app.config[typename]:
            logger.debug(f"using named config {typename}.{self.shortname}")
            config = self.app.config[typename][self.shortname]
            if extra and config:
                return core.DeepChain(extra, config)
            else:
                return extra or config
        logger.info(f"could not find config for {typename}.{self.shortname} in")
        return extra

    def kreate_file(self) -> None:
        filename = self.filename
        if filename:
            dir = self.dirname
            self.save_yaml(f"{dir}/{filename}")

    def _template_vars(self):
        return {
            "cfg" : self.config,
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

    def need_kustomize(self):
        return False

    @property
    def filename(self):
        return f"{self.kind.lower()}-{self.shortname}.yaml"


class Resource(YamlObject):
    def __init__(self,
                 app: App,
                 shortname: str = None,
                 kind: str = None,
                 template: str = None,
                 **kwargs
                ):
        YamlObject.__init__(self, app, kind=kind, shortname=shortname, template=template, **kwargs)
        self.add_metadata()

    def add_patches(self) -> None:
        for patch in self.config.get("patches", {}):
            if patch == "HttpProbesPatch":
                HttpProbesPatch(self)
            elif patch == "AntiAffinityPatch":
                AntiAffinityPatch(self)

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


class Kustomization(YamlObject):
    @property
    def resources(self):
        # exlcude ConfigMap if it should be generated by kustomize
        return [res for res in self.app.yaml_objects if isinstance(res, Resource) and not res.need_kustomize()  ]

    @property
    def config_maps(self):
        return [res for res in self.app.yaml_objects if isinstance(res, ConfigMap) and res.need_kustomize()  ]


    @property
    def patches(self):
        return [res for res in self.app.yaml_objects if isinstance(res, Patch)]

    @property
    def filename(self):
        return "kustomization.yaml"

class ConfigMap(Resource):
    def need_kustomize(self):
        return self.config.get("kustomize", True)

    def calc_name(self):
        return f"{self.app.name}-{self.shortname}"

    @property
    def filename(self) -> str:
        if self.need_kustomize():
            logger.debug(f"not kreating file for {self.name}, will be created by kustomize")
            return None
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

#########################################################################################
class Patch(YamlObject):
    def __init__(self, target: Resource, shortname: str = None, **kwargs):
        self.target = target
        YamlObject.__init__(self, target.app, shortname=shortname, **kwargs)

    def need_kustomize(self):
        return True

    def _template_vars(self):
        return { **super()._template_vars(),  "target": self.target }

    def _find_config(self, extra):
        root_config = super()._find_config(extra)
        typename = self.kind
        target_config = self.target.config.get("patches",{})
        if typename in target_config and self.shortname in target_config[typename]:
            logger.debug(f"using embedded config {typename}.{self.shortname} from {self.target.kind}.{self.target.shortname}")
            # The embedded_config is first, since the root_config will contain all default values
            embedded_config = target_config[typename][self.shortname]
            return core.DeepChain(embedded_config, root_config)
        return root_config


class HttpProbesPatch(Patch):
    pass
class AntiAffinityPatch(Patch):
    pass
