from . import templates
import os
import sys
from ruamel.yaml import YAML

script_directory = os.path.dirname(os.path.abspath(sys.argv[0]))


class App:
    def __init__(self, name: str, parent = None,
                 template_package=templates, image_name: str = None):
        self.name = name
        self.image_name = image_name or name + ".app"
        self.image_repo = "somewhere.todo/"
        self.vars = dict()
        vars_file = script_directory + "/vars-" + self.name + ".yaml"
        if parent:
            self.vars.update(parent.vars)
        if os.path.exists(vars_file):
            yaml=YAML()
            with open(vars_file) as f:
                self.vars.update(yaml.load(f))

        self.namespace = self.name + "-" + self.vars["env"]
        self.labels = dict()
        self.target_dir = "./build/target"
        self.template_package = template_package
        self.replicas=1
