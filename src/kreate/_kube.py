import os
import sys
import shutil
import inspect
import logging
from collections.abc import Mapping
from ._app import App
from ._komp import Komponent

logger = logging.getLogger(__name__)


class KubeApp(App):
    def _init(self):
        pass

    def register_std_templates(self) -> None:
        super().register_std_templates()
        self.register_template_class(Service, aliases="svc")
        self.register_template_class(Deployment, aliases="depl")
        self.register_template_class(PodDisruptionBudget, aliases="pdb")
        self.register_template_class(ConfigMap, aliases="cm")
        self.register_template_class(Ingress)
        self.register_template_class(Egress)
        self.register_template_file("HorizontalPodAutoscaler", aliases="hpa")
        self.register_template_file("ServiceAccount")
        self.register_template_file("ServiceMonitor")

    def kreate_komponent(self, kind: str, shortname: str = None, **kwargs):
        templ = self.templates[kind]
        if inspect.isclass(templ):
            return templ(self, shortname=shortname, kind=kind, **kwargs)
        else:
            # TODO: not everything is a Resource
            return Resource(self, shortname=shortname, kind=kind, template=templ , **kwargs)

    def kreate_resource(self, kind: str, shortname: str = None, **kwargs):
        return Resource(self, shortname=shortname, kind=kind, **kwargs)


##################################################################


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

    def __str__(self):
        return f"<Resource {self.kind}.{self.shortname} {self.name}>"

    @property
    def filename(self):
        # prefix the file, because the name of a resource is not guaranteed
        # to be unique
        return f"{self.kind}-{self.name}.yaml".lower()

    def add_metadata(self):
        for key in self.konfig.get("annotations", {}):
            if not "annotations" in self.yaml.metadata:
                self.yaml.metadata.annotations={}
            self.yaml.metadata.annotations[key]=self.konfig.annotations[key]
        for key in self.konfig.get("labels", {}):
            if not "labels" in self.yaml.metadata:
                self.yaml.metadata.labels={}
            self.yaml.metadata.labels[key]=self.konfig.labels[key]

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
