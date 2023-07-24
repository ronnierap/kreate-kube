from  ruamel.yaml import YAML
import os

parser = YAML()

def loadOptionalYaml(filename):
    if os.path.exists(filename):
        with open(filename) as f:
            return parser.load(f)
    else:
        return {}
