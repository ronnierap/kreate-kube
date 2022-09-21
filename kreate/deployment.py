import kreate
from .cont import Container


class Deployment(kreate.Base):
    def __init__(self, app: kreate.App):
        # self.replicas = env.replicas
        self.container = [Container('app')]
        self.container[0].image_name = app.name + ".app"
        kreate.Base.__init__(self, app, "Deployment")
