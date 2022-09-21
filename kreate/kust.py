import kreate


class Kustomization(kreate.Base):
    def __init__(self, app: kreate.App):
        self.name = "kustomization"
        self.resources = []
        self.patches = []
        kreate.Base.__init__(self, app, "Kustomization", Kustomization)

    def add(self, comp: kreate.Base):
        self.resources.append(comp)
        self.yaml.resources.append(comp.name+".yaml")
        return comp  # return to allow changing a freshly create component

    def patch(self, comp: kreate.Base):
        self.yaml.patches.append(comp)
        return comp  # return to allow changing a freshly create component

    def kreate(self):
        for rsrc in self.resources:
            rsrc.kreate()
        kreate.Base.kreate(self)
