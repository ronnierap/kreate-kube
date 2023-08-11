import logging
from ..kore._app import App, AppDef, b64encode
from ..kore._komp import Komponent
from ..kore._jinyaml import FileLocation
from ..krypt import _krypt
from . import templates

logger = logging.getLogger(__name__)


class KubeApp(App):
    def __init__(self, appdef: AppDef):
        appdef.values["dekrypt"]=_krypt.dekrypt_str
        _krypt._krypt_key = b64encode(appdef.yaml.get("krypt_key","no-krypt-key-defined"))
        super().__init__(appdef)

    def register_std_templates(self) -> None:
        super().register_std_templates()
        self.register_template_class(Service, aliases="svc", package=templates)
        self.register_template_class(Deployment, aliases="depl", package=templates)
        self.register_template_class(PodDisruptionBudget, aliases="pdb", package=templates)
        self.register_template_class(ConfigMap, aliases="cm", package=templates)
        self.register_template_class(Ingress, package=templates)
        self.register_template_class(Egress, package=templates)
        self.register_template_class(SecretBasicAuth, package=templates)
        self.register_template_file("HorizontalPodAutoscaler", aliases="hpa", package=templates)
        self.register_template_file("ServiceAccount", package=templates)
        self.register_template_file("ServiceMonitor", package=templates)
        self.register_template_file("Secret", package=templates)

    def register_template_file(self, kind:str, cls=None, filename=None, aliases=None, package=None):
        # Override parent, to provide default class Resource
        cls = cls or Resource
        super().register_template_file(kind, cls, filename=filename, aliases=aliases, package=package)


##################################################################
class Resource(Komponent):
    def __init__(self,
                 app: App,
                 shortname: str = None,
                 kind: str = None,
                 template: FileLocation = None,
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

    def load_file(self, filename: str) -> str:
        with open(f"{self.app.appdef.dir}/{filename}") as f:
            return f.read()


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


class SecretBasicAuth(Resource):
    def calc_name(self):
        return f"{self.app.name}-{self.shortname}"

    def users(self):
        result=[]
        for usr in self.konfig.users:
            entry = _krypt.dekrypt_str(self.app.values[usr])
            result.append(f"{usr}:{entry}")
        result.append("")  # for the final newline
        return "\n".join(result)


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

    def basic_auth(self, secret: str = None) -> None:
        secret = secret or f"{self.app.name}-basic-auth"
        self.nginx_annon("auth-type", "basic")
        self.nginx_annon("auth-secret", secret)
        self.nginx_annon("auth-realm", self.app.name + "-realm")
