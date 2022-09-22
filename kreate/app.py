from . import templates


class Environment:
    def __init__(self, name: str):
        self.name = name
        self.replicas = 1
        self.vars = dict()
        self.namespace = "demo-" + self.name

    def add_var(self, name: str, value: str) -> None:
        self.vars[name] = value


class App:
    def __init__(self, name: str,  version: str, env: Environment,
                 template_package=templates, image_name: str = None):
        self.name = name
        self.version = version
        self.env = env
        self.image_name = image_name or name + ".app"
        self.image_repo = "somewhere.todo/"
        self.labels = dict()
        self.target_dir = "./target"
        self.template_package = template_package
