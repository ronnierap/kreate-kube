class Environment:
    def __init__(self, name: str):
        self.name = name
        self.replicas = 1
        self.image_repo = "somewhere.todo/"
        self.vars = dict()
        self.namespace = "demo-" + self.name

    def add_var(self, name: str, value: str) -> None:
        self.vars[name] = value


class App:
    def __init__(self, name: str, env: Environment):
        self.name = name
        self.labels = dict()
        self.target_dir = "./target"
        self.env = env
