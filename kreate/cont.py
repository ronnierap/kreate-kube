class Container:
    def __init__(self, name: str):
        self.name = name
        self.cpu_limit = '500m'
        self.cpu_request = '500m'
        self.mem_limit = '512Mi'
        self.mem_request = '512Mi'
        self.image_version = 'v1'
        self.port = 8080
