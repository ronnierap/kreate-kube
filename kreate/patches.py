from .base import Base
from .app import App
from .resources import Resource

class Patch(Base):
    def __init__(self, target: Resource, template, name=None, filename=None):
        Base.__init__(self, target.app, name, filename, template=template)
        self.target =target
        self.target.patches.append  (self)

    def _add_jinja_vars(self, vars):
        vars["target"]=self.target


class HttpProbes(Patch):
    def __init__(self, target: Resource):
        Patch.__init__(self, target, "patch-http-probes.yaml", name=target.name+"-probes")
