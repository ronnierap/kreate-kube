import os
import sys
import shutil
from . import yaml, templates
#from .resources import Resource


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
        self._attr_map={}

    def add(self, res, abbrevs) -> None:
        self.resources.append(res)
        attr_name = res.name.replace("-","_").lower()
        self._attr_map[attr_name] = res
        for abbrev in abbrevs:
            abbrev = abbrev.replace("-","_").lower()
            if abbrev not in self._attr_map: # Do not overwrite
                self._attr_map[abbrev] = res
        if attr_name.startswith(self.name.lower()+"_"):
            short_name = attr_name[len(self.name)+1:]
            if short_name not in self._attr_map: # Do not overwrite
                self._attr_map[short_name] = res

    def __getattr__(self, attr):
        if attr in self.__dict__ or attr == "_dict":
            return super().__getattribute__(attr)
        return self._attr_map[attr]

    def kreate_resources(self):
        # TODO better place: to clear directory
        if os.path.exists(self.target_dir) and os.path.isdir(self.target_dir):
            shutil.rmtree(self.target_dir)
        os.makedirs(self.target_dir, exist_ok=True)

        for rsrc in self.resources:
            rsrc.kreate()
