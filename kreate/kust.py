from .base import Base
from .app import App


class ConfigMap(Base):
    def __init__(self, app: App):
        self.vars = {}
        Base.__init__(self, app, name=app.name+"-vars")

    def add_var(self, name):
        self.vars[name] = self.app.vars[name]
        self.yaml.data.add(name, self.app.vars[name])

class Kustomization(Base):
    def __init__(self, app: App, cm : ConfigMap = None):
        self.name = "kustomization"
        self.configmaps = [ cm ]
        Base.__init__(self, app, name="kustomization")
        self.yaml.resources._seq.pop() #delete("kustomization.yaml")
        self.yaml.resources._seq.remove(cm.filename)


    def add_cm(self, cm: ConfigMap):
        self.configmaps.append(cm)
        self.yaml.resources._seq.remove(cm.filename)
