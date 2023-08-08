import jinja2
import pkgutil
import logging
import importlib
import inspect
from collections.abc import Mapping
from ruamel.yaml import YAML
from collections import namedtuple

from ._core import wrap

logger = logging.getLogger(__name__)

yaml_parser = YAML()

class FileLocation(namedtuple("FileLocation", "filename package dir", defaults=[None, None])):
    __slots__ = ()
    def __str__(self):
        if self.package:
            return f"FileLocation({self.filename} @package:{self.package.__name__})"
        return f"FileLocation({self.filename} @dir {self.dir})"


def load_data(file_loc : FileLocation):
    filename = file_loc.filename
    dirname = file_loc.dir
    package = file_loc.package
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
        logger.debug(f"finding module {package_name}")
        package = importlib.import_module(package_name)
    if package:
        logger.debug(f"loading {filename} from package {package.__name__}")
        return pkgutil.get_data(package.__package__, filename).decode('utf-8')
    else:
        dirname = dirname or "."
        logger.debug(f"loading {filename} from {dirname}")
        with open(f"{dirname}/{filename}") as f:
            return f.read()

def load_jinja_data(file_loc : FileLocation, vars: Mapping):
    filedata = load_data(file_loc=file_loc)
    tmpl = jinja2.Template(
        filedata,
        undefined=jinja2.StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True
    )
    return tmpl.render(vars)

def load_yaml(file_loc : FileLocation) -> Mapping:
    return yaml_parser.load(load_data(file_loc=file_loc))

def load_jinyaml(file_loc : FileLocation, vars: Mapping) -> Mapping:
    return yaml_parser.load(load_jinja_data(file_loc=file_loc, vars=vars))

def dump(data, file):
    yaml_parser.dump(data, file)



class YamlBase:
    def __init__(self, template: FileLocation):
        self.template = template
        self.dir = dir

    def load_yaml(self):
        vars = self._template_vars()
        self.yaml = wrap(load_jinyaml(self.template, vars ))

    def save_yaml(self, outfile) -> None:
        with open(outfile, 'wb') as f:
            dump(self.yaml.data, f)

    def _template_vars(self):
        return {}
