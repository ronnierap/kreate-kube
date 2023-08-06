import jinja2
import pkgutil
import logging
import importlib

from collections.abc import Mapping
from ruamel.yaml import YAML

logger = logging.getLogger(__name__)

yaml_parser = YAML()

def load_data(filename: str, package=None, dirname: str = None):
    prefix = "py:"
    if filename.startswith(prefix):
        fname = filename[len(prefix):]
        if package:
            raise ValueError(f"filename {filename} specifies package, but package {package} is also provided")
        spl = fname.split(":",1) # split into package_name and filename between :
        if len(spl) < 2:
            raise ValueError(f"filename {filename} should be of format py:<package>:<file>")
        package_name = spl[0]
        filename = spl[1]
        package = importlib.import_module(package_name)
    if package:
        return pkgutil.get_data(package.__package__, filename).decode('utf-8')
    dirname = dirname or "."
    with open(f"{dirname}/{filename}") as f:
        return f.read()

def load_jinja_data(filename: str, vars: Mapping, package=None, dirname: str = None):
    filedata = load_data(filename, package=package, dirname=dirname)
    tmpl = jinja2.Template(
        filedata,
        undefined=jinja2.StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True
    )
    return tmpl.render(vars)

def load_yaml(filename: str, package=None, dirname: str = None) -> Mapping:
    logger.debug(f"loading yaml {filename} from {package or dirname or '.'}")
    return yaml_parser.load(load_data(filename, package=package, dirname=dirname))

def load_jinyaml(filename: str, vars: Mapping, package=None, dirname: str = None) -> Mapping:
    logger.debug(f"loading jinyaml {filename} from {package or dirname or '.'}")
    return yaml_parser.load(load_jinja_data(filename, vars, package=package, dirname=dirname))

def dump(data, file):
    yaml_parser.dump(data, file)
