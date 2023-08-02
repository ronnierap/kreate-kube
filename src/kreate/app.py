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


    def add(self, res) -> None:
        if not res.skip:
            self.resources.append(res)

        map = self._kinds.get(res.kind.lower(), None)
        if map is None:
            map = core.DictWrapper({})
            self._kinds[res.kind.lower()] = map
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
            Egress(self, none_if_main(shortname))
        for shortname in self._shortnames("Ingress"):
            Ingress(self, none_if_main(shortname))
        for shortname in self._shortnames("Deployment"):
            Deployment(self, none_if_main(shortname))
        for shortname in self._shortnames("Service"):
            Service(self, none_if_main(shortname))
        for shortname in self._shortnames("PodDisruptionBudget"):
            print(shortname)
            PodDisruptionBudget(self, shortname)
        for shortname in self._shortnames("ServiceAccount"):
            self.kreate("ServiceAccount", none_if_main(shortname))
        for shortname in self._shortnames("ServiceMonitor"):
            self.kreate("ServiceMonitor", none_if_main(shortname))



##################################################################

class Resource(core.YamlBase):
    def __init__(self, app: App,
                 shortname: str = None,
                 kind: str = None,
                 name: str = None,
                 filename: str = None,
                 skip: bool = False,
                 config = None):
        self.app = app
        if kind is None:
            self.kind = self.__class__.__name__
        else:
            self.kind = kind
        typename = self.kind.lower()
        if shortname is None:
            shortname = "main"
            self.name = name or f"{app.name}-{typename}"
        else:
            self.name = name or f"{app.name}-{typename}-{shortname}"
        self.shortname = shortname
        self.filename = filename or f"{self.name}.yaml"
        self.patches = []
        self.skip = skip

        if config:
            self.config = config
        elif self.kind in app.config and self.shortname in app.config[self.kind]:
            logger.debug(f"using named config {self.kind}.{shortname}")
            self.config = app.config[self.kind][shortname]
        elif typename in app.config:
            if self.shortname in app.config[typename]:
                logger.debug(f"using named config {typename}.{shortname}")
                self.config = app.config[typename][shortname]
            else:
                logger.debug(f"could not find config for {shortname} in {typename}.")
                self.config = {}
        else:
            logger.debug(f"could not find any config for {typename}")
            self.config = {}
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
        Resource.__init__(self, app, filename="kustomization.yaml", skip=True)


class Deployment(Resource):
    def __init__(self, app: App, shortname: str = None):
        if shortname is None:
            name = app.name
            filename = f"{app.name}-deployment.yaml"
        else:
            name = None
            filename = None
        Resource.__init__(self, app, shortname, name=name, filename=filename)

    def add_template_annotation(self, name: str, val: str) -> None:
        if not "annotations" in self.yaml.spec.template.metadata:
            self.yaml.spec.template.metadata["annotations"] = {}
        self.yaml.spec.template.metadata.annotations[name] = val

    def add_template_label(self, name: str, val: str) -> None:
        if not "labels" in self.yaml.spec.template.metadata:
            self.yaml.spec.template.metadata["labels"] = {}
        self.yaml.spec.template.metadata.labels[name] = val


class PodDisruptionBudget(Resource):
    def __init__(self, app: App, shortname: str = None):
        Resource.__init__(self, app, shortname, name=f"{app.name}-pdb")

class Service(Resource):
    def __init__(self, app: App, shortname : str = None):
        Resource.__init__(self, app, shortname=shortname)

    def headless(self):
        self.yaml.spec.clusterIP="None"

class Egress(Resource):
    def __init__(self, app: App, shortname: str):
        Resource.__init__(self, app, shortname=shortname, name=f"{app.name}-egress-to-{shortname}")

class ConfigMap(Resource):
    def __init__(self, app: App, shortname=None, name: str = None, kustomize=False):
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
            value = self.app.config.vars[name]
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
    def __init__(self, target: Resource, template, config: Mapping):
        self.target = target
        self.target.patches.append(self)
        self.config = config
        self.filename = template
        core.YamlBase.__init__(self, template=template)
        self.load_yaml()

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
        config = target.app.config.containers[container_name]
        Patch.__init__(self, target, "patch-http-probes.yaml", config=config)

class AntiAffinityPatch(Patch):
    def __init__(self, target: Resource, container_name : str ="app"):
        config = target.app.config.containers[container_name]
        Patch.__init__(self, target, "patch-anti-affinity.yaml", config=config)
