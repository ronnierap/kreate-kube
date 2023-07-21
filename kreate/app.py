from . import templates


class Environment:
    def __init__(self, name: str):
        self.name = name
        self.vars = dict()

    def add_var(self, name: str, value: str) -> None:
        self.vars[name] = value


class App:
    def __init__(self, name: str,  version: str, env: Environment,
                 template_package=templates, image_name: str = None):
        self.name = name
        self.version = version
        self.env = env
        self.namespace = self.name + "-" + self.env.name
        self.image_name = image_name or name + ".app"
        self.image_repo = "somewhere.todo/"
        self.labels = dict()
        self.target_dir = "./build/target"
        self.template_package = template_package
        self.replicas=1
