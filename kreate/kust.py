from .base import Base
from .app import App


class Kustomization(Base):
    def __init__(self, app: App):
        self.name = "kustomization"
        Base.__init__(self, app, name="kustomization")
        self.yaml.resources._seq.pop() #delete("kustomization.yaml")

class ConfigMap(Base):
    def __init__(self, app: App):
        self.vars = {}
        Base.__init__(self, app, name=app.name+"-vars")

    def add_var(self, name):
        self.vars[name] = self.app.vars[name]
        self.yaml.data.add(name, self.app.vars[name])
