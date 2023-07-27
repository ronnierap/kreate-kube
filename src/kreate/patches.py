from .yaml import YamlBase
from .app import App
from .resources import Resource

class Patch(YamlBase):
    def __init__(self, target: Resource, template, name=None, filename=None):
        self.target =target
        self.target.patches.append  (self)
        YamlBase.__init__(self, target.app, name, filename, template=template)

    def _add_jinja_vars(self, vars):
        vars["target"]=self.target


class HttpProbesPatch(Patch):
    def __init__(self, target: Resource):
        Patch.__init__(self, target, "patch-http-probes.yaml", name=target.name+"-probes")

class AntiAffinityPatch(Patch):
    def __init__(self, target: Resource):
        Patch.__init__(self, target, "patch-anti-affinity.yaml", name=target.name+"-anti-affinity")
