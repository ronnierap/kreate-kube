from .base import Base
from .app import App

class Resource(Base):
    def __init__(self, app: App, name=None, filename=None):
        Base.__init__(self, app, name, filename)
        self.app.resources.append(self)
        patches = {}

class Patch(Base):
    def __init__(self, target: Resource, name=None, filename=None):
        Base.__init__(self, target.app, name, filename)
        self.target =target
        self.target.patches.append(self)

class Deployment(Resource):
    def __init__(self, app: App):
        # self.replicas = env.replicas
        # self.container = [Container('app')]
        # self.container[0].image_name = app.name + ".app"
        Resource.__init__(self, app, name=app.name, filename=app.name+"-deployment.yaml")

    def add_template_annotation(self, name: str, val: str) -> None:
        if not self.yaml.spec.template.metadata.has_key("annotations"):
            self.yaml.spec.template.metadata.add("annotations", {})
        self.yaml.spec.template.metadata.annotations.add(name, val)

    def add_template_label(self, name: str, val: str) -> None:
        if not self.yaml.spec.template.metadata.has_key("labels"):
            self.yaml.spec.template.metadata.add("labels", {})
        self.yaml.spec.template.metadata.labels.add(name, val)

class PodDisruptionBudget(Resource):
    def __init__(self, app: App):
        Resource.__init__(self, app)


class ConfigMap(Resource):
    def __init__(self, app: App):
        self.vars = {}
        Resource.__init__(self, app)

    def add_var(self, name):
        self.vars[name] = self.app.vars[name]
        self.yaml.data.add(name, self.app.vars[name])
