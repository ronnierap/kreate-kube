from .base import Base
from .app import App


class Deployment(Base):
    def __init__(self, app: App):
        # self.replicas = env.replicas
        # self.container = [Container('app')]
        # self.container[0].image_name = app.name + ".app"
        Base.__init__(self, app)


class Container:
    def __init__(self, name: str):
        self.name = name
        self.cpu_limit = '500m'
        self.cpu_request = '500m'
        self.mem_limit = '512Mi'
        self.mem_request = '512Mi'
        self.port = 8080
