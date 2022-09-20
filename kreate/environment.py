
class Environment:
    def __init__(self, name: str):
        self.name = name
        self.replicas = 1
        self.image_repo = "somewhere.todo/"
        self.vars = dict()

    def add_var(self, name: str, value: str) -> None:
        self.vars[name] = value
