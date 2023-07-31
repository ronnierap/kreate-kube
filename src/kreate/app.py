import os
import sys
import shutil
from collections.abc import Mapping

from . import templates, core

class App:
    def __init__(self, name: str,
                 env : str,
                 template_package=templates,
                 config_dir : str =".",
                 config: Mapping = None,
                 kustomize: bool =False):
        self.name = name
        self.script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.vars = dict()
        self.config = config
        self.kustomize = kustomize
        vars_file = f"{self.script_dir}/env/{env}/vars-{self.name}-{env}.yaml"
        self.vars.update(core.loadOptionalYaml(vars_file))
        self.namespace = self.name + "-" + self.config["env"]
        self.target_dir = "./build/" + self.namespace
        self.template_package = template_package
        self.resources=[]
        self._attr_map={}

    def add(self, res, abbrevs) -> None:
        self.resources.append(res)
        attr_name = res.name.replace("-","_").lower()
        self._attr_map[attr_name] = res
        for abbrev in abbrevs:
            abbrev = abbrev.replace("-","_").lower()
            if abbrev not in self._attr_map: # Do not overwrite
                self._attr_map[abbrev] = res
        if attr_name.startswith(self.name.lower()+"_"):
            short_name = attr_name[len(self.name)+1:]
            if short_name not in self._attr_map: # Do not overwrite
                self._attr_map[short_name] = res

    def __getattr__(self, attr):
        if attr in self.__dict__ or attr == "_dict":
            return super().__getattribute__(attr)
        return self._attr_map[attr]

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



class Kustomization(core.YamlBase):
    def __init__(self, app: App):
        self.name = "kustomization"
        self.configmaps = []
        core.YamlBase.__init__(self, app, name="kustomization")


class GeneratedConfigMap(core.YamlBase):
    def __init__(self, kust:  Kustomization):
        self.vars = {}
        core.YamlBase.__init__(self, kust.app)

    def add_var(self, name):
        self.vars[name] = self.app.vars[name]
        self.yaml.data.add(name, self.app.vars[name])

##################################################################

class Resource(core.YamlBase):
    def __init__(self, app: App, name=None, filename=None, abbrevs=[], config=None):
        core.YamlBase.__init__(self, app, name, filename, config)
        if not self.ignored:
            self.app.add(self, abbrevs=abbrevs)
        self.patches = []

    def kreate(self) -> None:
        core.YamlBase.kreate(self)
        for p in self.patches:
            p.kreate()


class Deployment(Resource):
    def __init__(self, app: App):
        # self.replicas = env.replicas
        # self.container = [Container('app')]
        # self.container[0].image_name = app.name + ".app"
        Resource.__init__(self, app, name=app.name, filename=app.name+"-deployment.yaml", abbrevs=["depl","deployment"])

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
    def __init__(self, app: App, name=None, ports=[{"port": 8080}]):
        self.ports=ports
        Resource.__init__(self, app, name=name, abbrevs=["svc"])

    def headless(self):
        self.yaml.spec.clusterIP="None"

class Egress(Resource):
    pass

class ConfigMap(Resource):
    def __init__(self, app: App, name=None):
        self.vars = {}
        Resource.__init__(self, app, name=name, abbrevs=["cm"])

    def add_var(self, name, value=None):
        if value is None:
            value = self.app.vars[name]
        self.vars[name] = value
        # We can not use self.yaml.data, since data is a field in UserDict
        self.yaml["data"][name] = value


class Ingress(Resource):
    def __init__(self,
                 app: App,
                 name="root",
                 path="/",
                 host="TODO",
                 port=8080):
        self.path = path
        self.host = host
        self.port = port
        Resource.__init__(self, app, name=app.name + "-ingress-" + name) # TODO, config=app.config.ingress[name])

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
