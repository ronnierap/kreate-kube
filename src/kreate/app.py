import os
import sys
import shutil
from collections.abc import Mapping

from . import templates, core

class App:
    def __init__(self, name: str,
                 env : str,
                 config_dir : str =".",
                 config: Mapping = None,
                 kustomize: bool =False):
        self.name = name
        self.script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.vars = dict()
        self.config = config
        self.kustomize = kustomize
        self.namespace = self.name + "-" + self.config["env"]
        self.target_dir = "./build/" + self.namespace
        self.resources = []
        self._attr_map = {}
        self._kinds = {}

    def add(self, res, abbrevs) -> None:
        self.resources.append(res)
        attr_name = res.name.replace("-","_").lower()
        self._attr_map[attr_name] = res
        #for abbrev in abbrevs:
        #    abbrev = abbrev.replace("-","_").lower()
        #    if abbrev not in self._attr_map: # Do not overwrite
        #        self._attr_map[abbrev] = res
        map = self._kinds.get(res.kind.lower(), None)
        if map is None:
            map = core.DictWrapper({})
            self._kinds[res.kind.lower()] = map
        #if attr_name.startswith(self.name.lower()+"_"):
        #    short_name = attr_name[len(self.name)+1:]
        #    if short_name not in self._attr_map: # Do not overwrite
        #        self._attr_map[short_name] = res
        map[res.name] = res

    def __getattr__(self, attr):
        if attr in self.__dict__ or attr == "_dict":
            return super().__getattribute__(attr)
        return self._kinds.get(attr, None)

    def kreate_files(self):
        # TODO better place: to clear directory
        if os.path.exists(self.target_dir) and os.path.isdir(self.target_dir):
            shutil.rmtree(self.target_dir)
        os.makedirs(self.target_dir, exist_ok=True)

        for rsrc in self.resources:
            rsrc.kreate()
        if self.kustomize:
            kust = Kustomization(self)
            kust.kreate()

class Strukture(App):
    def __init__(self, name: str, env: str, config: Mapping):
        super().__init__(name, env, config=config)
        for name in config.egress.keys():
            Egress(self, name)
        for name in config.ingress.keys():
            Ingress(self, name)
        #Deployment(self, self.name)



##################################################################

class Resource(core.YamlBase):
    def __init__(self, app: App, name=None, kind: str = None, abbrevs=[], config=None):
        self.app = app
        if kind is None:
            self.kind = self.__class__.__name__
        else:
            self.kind = kind
        self.name = name
        typename = self.kind.lower()
        self.fullname = f"{app.name}-{typename}-{name}"
        self.filename = f"{self.app.target_dir}/{self.fullname}.yaml"
        self.patches = []

        if config:
            self.config = config
        else:
            if typename in app.config and name in app.config[typename]:
                #print(f"DEBUG using config {typename}.{name}")
                self.config = app.config[typename][name]
                #print(self.config)
            else:
                print(f"DEBUG could not find config {typename}.{name}")
                self.config = {}
        template = f"{self.kind}.yaml"
        core.YamlBase.__init__(self, template)
        if self.config.get("ignore", False):
            # config indicates to be ignored
            # - do not load the template (config might be missing)
            # - do not register
            print(f"INFO: ignoring {typename}.{self.name}")
            self.ignored = True
        else:
            self.ignored = False
            self.app.add(self, abbrevs=abbrevs)
            self.load_yaml()

    def _get_jinja_vars(self):
        return {
            "app": self.app,
            "cfg": self.config,
            "my": self,
        }

    def kreate(self) -> None:
        self.save_yaml(self.filename)
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
        Resource.__init__(self, app, name="kusst")


class Deployment(Resource):
    def __init__(self, app: App):
        # self.replicas = env.replicas
        # self.container = [Container('app')]
        # self.container[0].image_name = app.name + ".app"
        Resource.__init__(self, app, name=app.name, abbrevs=["depl","deployment"])
        # filename=app.name+"-deployment.yaml",

    def add_template_annotation(self, name: str, val: str) -> None:
        if not self.yaml.spec.template.metadata.has_key("annotations"):
            self.yaml.spec.template.metadata.add("annotations", {})
        self.yaml.spec.template.metadata.annotations.add(name, val)

    def add_template_label(self, name: str, val: str) -> None:
        if not self.yaml.spec.template.metadata.has_key("labels"):
            self.yaml.spec.template.metadata.add("labels", {})
        self.yaml.spec.template.metadata.labels.add(name, val)


class PodDisruptionBudget(Resource):
    def __init__(self, app: App, name=None):
        Resource.__init__(self, app, name=name, abbrevs=["pdb"])

class Service(Resource):
    def __init__(self, app: App, name=None):
        Resource.__init__(self, app, name=name, abbrevs=["svc"])

    def headless(self):
        self.yaml.spec.clusterIP="None"

class Egress(Resource):
    def __init__(self, app: App, name: str):
        Resource.__init__(self, app, name=name) #=app.name + "-egress-to-" + name) # TODO, config=app.config.ingress[name])

class ConfigMap(Resource):
    def __init__(self, app: App, name=None, kustomize=False):
        self.kustomize = kustomize
        Resource.__init__(self, app, name=name, abbrevs=["cm"])
        if kustomize:
            app.kustomize = True
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
    def __init__(self, app: App, name: str ="root", path: str ="/" ):
        self.path = path
        Resource.__init__(self, app, name) # TODO, config=app.config.ingress[name])

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
    def __init__(self, target: Resource, template, name=None, filename=None, config=None):
        self.target =target
        self.target.patches.append  (self)
        core.YamlBase.__init__(self, target.app, name, filename, template=template, config=config)

    def _add_jinja_vars(self, vars):
        vars["target"]=self.target


class HttpProbesPatch(Patch):
    def __init__(self, target: Resource, container_name : str ="app"):
        config = target.app.config.containers[container_name]
        Patch.__init__(self, target, "patch-http-probes.yaml", name=target.name+"-probes", config=config)

class AntiAffinityPatch(Patch):
    def __init__(self, target: Resource, container_name : str ="app"):
        config = target.app.config.containers[container_name]
        Patch.__init__(self, target, "patch-anti-affinity.yaml", name=target.name+"-anti-affinity", config=config)
