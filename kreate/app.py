from . import templates
import os
import sys
import shutil
from . import yaml

class App:
    def __init__(self, name: str, parent = None,
                 template_package=templates, image_name: str = None):
        self.name = name
        self.vars = dict()
        self.config = dict()
        script_directory = os.path.dirname(os.path.abspath(sys.argv[0]))
        if parent:
            self.vars.update(parent.vars)
            self.config.update(parent.config)
        vars_file = script_directory + "/vars-" + self.name + ".yaml"
        self.vars.update(yaml.loadOptionalYaml(vars_file))
        config_file = script_directory + "/config-" + self.name + ".yaml"
        self.config.update(yaml.loadOptionalYaml(config_file))

        self.namespace = self.name + "-" + self.config["env"]
        #self.labels = dict()
        self.target_dir = "./build/" + self.namespace
        self.template_package = template_package
        self.resources=[]

    def kreate_resources(self):
        # TODO better place: to clear directory
        if os.path.exists(self.target_dir) and os.path.isdir(self.target_dir):
            shutil.rmtree(self.target_dir)
        os.makedirs(self.target_dir, exist_ok=True)

        for rsrc in self.resources:
            rsrc.kreate()
