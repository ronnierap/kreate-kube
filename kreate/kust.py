from .base import Base
from .app import App


class Kustomization(Base):
    def __init__(self, app: App):
        self.name = "kustomization"
        self.resources = []
        self.patches = []
        Base.__init__(self, app, "Kustomization", Kustomization)

    def add(self, comp: Base):
        self.resources.append(comp)
        return comp  # return to allow changing a freshly create component

    def patch(self, comp: Base):
        self.patches.append(comp)
        return comp  # return to allow changing a freshly create component

    def kreate(self):
        for rsrc in self.resources:
            rsrc.kreate()
        for patch in self.patches:
            patch.kreate()
        Base.kreate(self)
