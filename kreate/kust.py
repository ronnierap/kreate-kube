import kreate


class Kustomization(kreate.Base):
    def __init__(self, app: kreate.App):
        kreate.Base.__init__(self, app, "Kustomization")
        self.name = "kustomization"
        self.resources = []
        self.patches = []
        self.vars = {}

    def add(self, comp: kreate.Base):
        self.resources.append(comp)
        return comp # return to allow changing a freshly create component

    def patch(self, comp: kreate.Base):
        self.patches.append(comp)
        return comp # return to allow changing a freshly create component


    def kreate(self, env: kreate.Environment):
        for rsrc in self.resources:
          rsrc.kreate(env)
        kreate.Base.kreate(self,env)
