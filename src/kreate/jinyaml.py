import jinja2
import pkgutil
import logging

from collections.abc import Mapping
from ruamel.yaml import YAML

logger = logging.getLogger(__name__)

yaml_parser = YAML()

def load_data(filename: str, package=None):
    if package:
        print(package)
        return pkgutil.get_data(package.__package__, filename).decode('utf-8')
    with open(filename) as f:
        return f.read()


def load_yaml(filename: str, package=None) -> Mapping:
    # TODO: it might be more efficient to parse the file
    #if package is None: return parser.load(f)
    return yaml_parser.load(load_data(filename, package=package))

def load_jinja(filename: str, vars: Mapping, package=None):
    filedata = load_data(filename, package=package)
    tmpl = jinja2.Template(
        filedata,
        undefined=jinja2.StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True
    )
    return tmpl.render(vars)

def load_jinyaml(filename: str, vars: Mapping, package=None) -> Mapping:
    return yaml_parser.load(load_jinja(filename, vars, package=package))
