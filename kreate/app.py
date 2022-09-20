import jinja2
import shutil
import os


class App:
    def __init__(self, name: str,
                 kind: str = 'Deployment'):
        self.name = name
        self.kind = kind
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
