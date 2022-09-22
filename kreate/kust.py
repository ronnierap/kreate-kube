import shutil
import os

from .base import Base
from .app import App


class Kustomization(Base):
    def __init__(self, app: App):
        self.name = "kustomization"
        self.resources = []
        self.patches = []
        Base.__init__(self, app, name="kustomization")

    def add(self, comp: Base):
        self.resources.append(comp)
        return comp  # return to allow changing a freshly create component

    def patch(self, comp: Base):
        self.patches.append(comp)
        return comp  # return to allow changing a freshly create component

    def kreate(self):
        # TODO better place: to clear directory
        shutil.rmtree(self.app.target_dir)
        os.makedirs(self.app.target_dir, exist_ok=True)

        for rsrc in self.resources:
            rsrc.kreate()
        for patch in self.patches:
            patch.kreate()
        Base.kreate(self)
