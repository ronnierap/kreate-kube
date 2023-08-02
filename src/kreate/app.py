import os
import sys
import shutil
from collections.abc import Mapping
import logging

from . import core

logger = logging.getLogger(__name__)

def none_if_main(shortname: str) -> str:
    if shortname == "main":
        return None
    return shortname

class App():
    def __init__(
            self,
            name: str,
            env: str,
            config: core.Config = None,
            kustomize: bool =False,
        ):
        self.name = name
        self.script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.vars = dict()
        self.config = config.config()
        self.values = config.values()
        self.kustomize = kustomize
        self.env = env
        self.namespace = self.name + "-" + self.env
        self.target_dir = "./build/" + self.namespace
        self.resources = []
        self.kust_resources = []
        self._kinds = {}
        self.aliases = {}
        self.add_alias( "Service", "svc")
        self.add_alias( "Deployment", "depl")
        self.add_alias( "PodDisruptionBudget", "pdb")
        self.add_alias( "ConfigMap", "cm")

    def add_alias(self, kind: str, *aliases: str ):
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
            self.resources.append(res)
        map = self._kinds.get(res.kind, None)
        if map is None:
            map = core.DictWrapper({})
            self.get_aliases(res.kind)
            for alias in self.get_aliases(res.kind):
                self._kinds[alias] = map

        if res.shortname is None:
            map["_"] = res
        else:
            map[res.shortname] = res

    def __getattr__(self, attr):
        if attr in self.__dict__ or attr == "_dict":
            return super().__getattribute__(attr)
        return self._kinds.get(attr, None)

    def kreate(self, kind: str, shortname: str = None, fullname: str = None):
        res = Resource(self, shortname=shortname, kind=kind)

    def kreate_files(self):
        if os.path.exists(self.target_dir) and os.path.isdir(self.target_dir):
            shutil.rmtree(self.target_dir)
        os.makedirs(self.target_dir, exist_ok=True)

        for rsrc in self.resources:
            rsrc.kreate()
        if self.kustomize:
            kust = Kustomization(self)
            kust.kreate()

    def _shortnames(self, kind:str ) -> list:
        if kind in self.config:
            return [none_if_main(k) for k in self.config[kind].keys()]
        elif kind.lower() in self.config:
            return [none_if_main(k) for k in self.config[kind.lower()].keys()]
        else:
            return []


    def kreate_strukture(self):
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

        for shortname in self._shortnames("ServiceAccount"):
            self.kreate("ServiceAccount", shortname)
        for shortname in self._shortnames("ServiceMonitor"):
            self.kreate("ServiceMonitor", shortname)



##################################################################

class Resource(core.YamlBase):
    def __init__(self, app: App,
                 shortname: str = None,
                 kind: str = None,
                 name: str = None,
                 skip: bool = False,
                 config = None):
        self.app = app
        if kind is None:
            self.kind = self.__class__.__name__
        else:
            self.kind = kind

        self.shortname = shortname or "main"
        self.config = config or self._find_config()

        typename = self.kind.lower()
        if shortname is None:
            self.name = name or self.config.get("name", f"{app.name}-{typename}")
        else:
            self.name = name or self.config.get("name", f"{app.name}-{typename}-{shortname}")

        self.filename = f"{typename}-{self.name}.yaml"
        # TODO: is there any reason to customize the filename?
        #self.filename = self.config.get("filename", f"{typename}-{self.name}.yaml")
        self.patches = []
        self.skip = skip

        template = f"{self.kind}.yaml"
        core.YamlBase.__init__(self, template)
        if self.config.get("ignore", False):
            # config indicates to be ignored
            # - do not load the template (config might be missing)
            # - do not register
            logger.info(f"ignoring {typename}.{self.name}")
            self.skip = True
        else:
            self.load_yaml()
        self.app.add(self)
        self.add_metadata()
        kreate_patches(self)

    def add_metadata(self):
        for key in self.config.get("annotations", {}):
            if not "annotations" in self.yaml.metadata:
                self.yaml.metadata.annotations={}
            self.yaml.metadata.annotations[key]=self.config.annotations[key]
        for key in self.config.get("labels", {}):
            if not "labels" in self.yaml.metadata:
                self.yaml.metadata.labels={}
            self.yaml.metadata.labels[key]=self.config.labels[key]

    def _find_config(self):
        # In theory we could use any kind_alias for finding the config with the code below
        #    for typename in app.get_aliases(self.kind):
        #        if typename in app.config and self.shortname in app.config[typename]:
        #            logger.debug(f"using named config {typename}.{shortname}")
        #            self.config = app.config[typename][shortname]
        #            break
        # This works, but has several drawbacks:
        # - Service.main could shadow svc.main, it needs to merge all found maps
        # - kreate_strukture, needs to iterate over all possible aliases
        # it seems doable, but can be confusing and for very little convenience
        typename = self.kind
        if typename in self.app.config and self.shortname in self.app.config[typename]:
            logger.debug(f"using named config {typename}.{self.shortname}")
            return self.app.config[typename][self.shortname]
        logger.warn(f"could not find config for {typename}.{self.shortname} in")
        return {} # TODO: should this be wrapped?


    def _get_jinja_vars(self):
        return {
            "app": self.app,
            "cfg": self.config,
            "my": self,
            "val": self.app.values
        }

    def kreate(self) -> None:
        self.save_yaml(f"{self.app.target_dir}/{self.filename}")
        for p in self.patches:
            p.kreate()

    def annotate(self, name: str, val: str) -> None:
        if "annotations" not in self.yaml.metadata:
            self.yaml.metadata["annotations"]={}
        self.yaml.metadata.annotations[name]=val

    def add_label(self, name: str, val: str) -> None:
        if "labels" not in self.yaml.metadata:
            self.yaml.metadata["labels"]={}
        self.yaml.metadata.labels[name]=val

class Kustomization(Resource):
    def __init__(self, app: App):
        Resource.__init__(self, app, skip=True)
        self.filename="kustomization.yaml"


class Deployment(Resource):
    def __init__(self, app: App, shortname: str = None):
        name = None if shortname else app.name
        Resource.__init__(self, app, shortname, name=name)

    def add_template_annotation(self, name: str, val: str) -> None:
        if not "annotations" in self.yaml.spec.template.metadata:
            self.yaml.spec.template.metadata["annotations"] = {}
        self.yaml.spec.template.metadata.annotations[name] = val

    def add_template_label(self, name: str, val: str) -> None:
        if not "labels" in self.yaml.spec.template.metadata:
            self.yaml.spec.template.metadata["labels"] = {}
        self.yaml.spec.template.metadata.labels[name] = val


class PodDisruptionBudget(Resource):
    pass

class Service(Resource):
    def headless(self):
        self.yaml.spec.clusterIP="None"

class Egress(Resource):
    # TODO: do we want a special class just for the egress-to-.... name?
    def __init__(self, app: App, shortname: str):
        Resource.__init__(self, app, shortname=shortname, name=f"{app.name}-egress-to-{shortname}")

class ConfigMap(Resource):
    def __init__(
            self,
            app: App,
            shortname: str = None,
            name: str = None,
            kustomize: bool = False
        ):
        self.kustomize = kustomize
        Resource.__init__(self, app, shortname=shortname, name=name, skip=kustomize)
        if kustomize:
            app.kustomize = True
            app.kust_resources.append(self)
            self.fieldname = "literals"
            self.yaml[self.fieldname] = {}
        else:
            self.fieldname = "data"


    def add_var(self, name, value=None):
        if value is None:
            value = self.app.values[name]
        # We can not use self.yaml.data, since data is a field in UserDict
        self.yaml[self.fieldname][name] = value


class Ingress(Resource):
    def __init__(self, app: App, shortname: str ="root"):
        Resource.__init__(self, app, shortname=shortname)

    def nginx_annon(self, name: str, val: str) -> None:
        self.annotate("nginx.ingress.kubernetes.io/" + name, val)

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
class Patch(core.YamlBase):
    def __init__(self, target: Resource, template):
        self.target = target
        self.target.patches.append(self)
        self.filename = template
        core.YamlBase.__init__(self, template=template)

    def kreate(self) -> None:
        self.save_yaml(f"{self.target.app.target_dir}/{self.filename}")

    def _get_jinja_vars(self):
        return {
            "target": self.target,
            "cfg" : self.config,
            "app" : self.target.app,
            "my" : self,
            "val": self.target.app.values
        }


class HttpProbesPatch(Patch):
    def __init__(self, target: Resource, container_name : str ="app"):
        self.config = target.app.config.containers[container_name]
        if self.config is None:
            (f"Unknown contrainer {container_name} to patch")
            raise ValueError(f"Unknown container name {container_name} to patch with HttpProbes")
        Patch.__init__(self, target, "patch-http-probes.yaml")
        self.load_yaml()

class AntiAffinityPatch(Patch):
    def __init__(self, target: Resource, selector_key : str ="app"):
        self.config = { "selector_key": selector_key }
        Patch.__init__(self, target, "patch-anti-affinity.yaml")
        self.load_yaml()

def kreate_patches(target : Resource) -> None:
    for patch in target.config.get("patches", {}):
        conf = target.config.patches[patch];
        if patch == "HttpProbesPatch":
            HttpProbesPatch(target, container_name=conf.get("container","app")) # TODO: do not mirror default value
        elif patch == "AntiAffinityPatch":
            AntiAffinityPatch(target, selector_key=conf.get("selector_key","app")) # TODO: do not mirror default value
