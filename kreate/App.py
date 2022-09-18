import kreate.Environment
import jinja2
import shutil
import os


class App:
    def __init__(self, name: str,
                 env: kreate.Environment,
                 kind: str = 'Deployment'):
        self.name = name
        self.env = env
        self.kind = kind
        self.replicas = env.replicas
        self.container = [Container('app')]
        self.container[0].image_name = env.image_repo + name + ".app"
        self.labels = dict()
        self.target_dir = "./target"

    def kreate_file(self, name: str, template: str) -> None:
        os.makedirs(self.target_dir, exist_ok=True)
        tmpl = jinja2.Template(
            template,
            undefined=jinja2.StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True)
        tmpl.stream(app=self, env=self.env).dump(self.target_dir+"/"+name)
        print(tmpl.render(app=self, env=self.env))

    def __clear(self) -> None:
        shutil.rmtree(self.target_dir)


class Container:
    def __init__(self, name: str):
        self.name = name
        self.cpu_limit = '500m'
        self.cpu_request = '500m'
        self.mem_limit = '512Mi'
        self.mem_request = '512Mi'
        self.port = 8080
