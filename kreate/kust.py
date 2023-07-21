from .base import Base
from .app import App


class Kustomization(Base):
    def __init__(self, app: App):
        self.name = "kustomization"
        Base.__init__(self, app, name="kustomization")
