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
    def __init__(self, app: App):
        self.name = "kustomization"
        self.configmaps = []
        Base.__init__(self, app, name="kustomization")
        #self.yaml.resources._seq.pop() #delete("kustomization.yaml")
        #self.yaml.resources._seq.remove(cm.filename)

    def kreate(self) -> None:
        self.yaml.resources._seq.pop() #delete("kustomization.yaml")
        Base.kreate(self)

    def add_cm(self, cm: ConfigMap):
        self.configmaps.append(cm)
        cm.app.resources.remove(cm)
        #print(cm.filename)
        #print(self.yaml.resources._seq)
        #self.yaml.resources._seq.remove(cm.filename)
