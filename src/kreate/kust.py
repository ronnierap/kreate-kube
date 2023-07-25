from .base import Base
from .app import App


class Kustomization(Base):
    def __init__(self, app: App):
        self.name = "kustomization"
        self.configmaps = []
        Base.__init__(self, app, name="kustomization")

    def kreate_files(self) -> None:
        self.app.kreate_resources()
        self.kreate()


#    def add_cm(self, cm: ConfigMap):
#        self.configmaps.append(cm)
#        cm.app.resources.remove(cm)


class GeneratedConfigMap(Base):
    def __init__(self, kust:  Kustomization):
        self.vars = {}
        Base.__init__(self, kust.app)

    def add_var(self, name):
        self.vars[name] = self.app.vars[name]
        self.yaml.data.add(name, self.app.vars[name])
