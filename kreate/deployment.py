from .base import Base
from .app import App


class Deployment(Base):
    def __init__(self, app: App):
        # self.replicas = env.replicas
        # self.container = [Container('app')]
        # self.container[0].image_name = app.name + ".app"
        Base.__init__(self, app, name=app.name, filename=app.name+"-deployment.yaml")

    def add_template_annotation(self, name: str, val: str) -> None:
        if not self.yaml.spec.template.metadata.has_key("annotations"):
            self.yaml.spec.template.metadata.add("annotations", {})
        self.yaml.spec.template.metadata.annotations.add(name, val)

    def add_template_label(self, name: str, val: str) -> None:
        if not self.yaml.spec.template.metadata.has_key("labels"):
            self.yaml.spec.template.metadata.add("labels", {})
        self.yaml.spec.template.metadata.labels.add(name, val)

class Container:
    def __init__(self, name: str):
        self.name = name
        self.cpu_limit = '500m'
        self.cpu_request = '500m'
        self.mem_limit = '512Mi'
        self.mem_request = '512Mi'
        self.port = 8080

class PodDisruptionBudget(Base):
    def __init__(self, app: App):
        Base.__init__(self, app)
