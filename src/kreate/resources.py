from .base import Base
from .app import App

class Resource(Base):
    def __init__(self, app: App, name=None, filename=None, abbrevs=[]):
        Base.__init__(self, app, name, filename)
        self.app.add(self, abbrevs=abbrevs)
        self.patches = []

    def kreate(self) -> None:
        Base.kreate(self)
        for p in self.patches:
            p.kreate()

class Patch(Base):
    def __init__(self, target: Resource, name=None, filename=None):
        Base.__init__(self, target.app, name, filename)
        self.target =target
        self.target.patches.add(self)


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
        Resource.__init__(self, app, name=name, abbrevs=["pdb"])

    def headless(self):
        self.yaml.spec.clusterIP="None"


class ConfigMap(Resource):
    def __init__(self, app: App, name=None):
        self.vars = {}
        Resource.__init__(self, app, name=name, abbrevs=["cm"])

    def add_var(self, name, value=None):
        if value is None:
            value = self.app.vars[name]
        self.vars[name] = value
        self.yaml.data.add(name, value)


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
        Resource.__init__(self, app, name=app.name + "-ingress-" + name)

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
