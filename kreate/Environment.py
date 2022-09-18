
class Environment:
    def __init__(self, name):
        self.name = name
        self.replicas = 1
        self.image_repo = "somewhere.todo/"
        self.vars = dict()

    def add_var(self, name, value):
        self.vars[name] = value
