import jinja2
import pkgutil
import logging
import importlib
from collections.abc import Mapping
from ruamel.yaml import YAML
from collections import namedtuple

logger = logging.getLogger(__name__)


yaml_parser = YAML()


class FileLocation(
    namedtuple("FileLocation", "filename package dir", defaults=[None, None])
):
    __slots__ = ()

    def __str__(self):
        if self.package:
            return f"py:{self.package.__name__}:{self.filename}"
        return f"{self.dir}/{self.filename}"

    def __repr__(self):
        if self.package:
            return (
                f"FileLocation({self.filename}"
                f" @package:{self.package.__name__})"
            )
        return f"FileLocation({self.filename} @dir {self.dir})"


# dirty hack to remember which file is being processed
_current_jinja_file = None


def load_data(file_loc: FileLocation):
    filename = file_loc.filename
    dirname = file_loc.dir
    package = file_loc.package
    prefix = "py:"
    if filename.startswith(prefix):
        fname = filename[len(prefix) :]
        if package:
            raise ValueError(
                f"filename {filename} specifies package, "
                f"but package {package} is also provided"
            )
        # split into package_name and filename between :
        spl = fname.split(":", 1)
        if len(spl) < 2:
            raise ValueError(
                f"filename {filename} should be of format py:<package>:<file>"
            )
        package_name = spl[0]
        filename = spl[1]
        logger.debug(f"loading file {filename} from package {package_name}")
        logger.debug(f"finding module {package_name}")
        package = importlib.import_module(package_name)
        return pkgutil.get_data(package.__package__, filename).decode("utf-8")
    elif package:
        logger.debug(
            f"loading file {filename} from package {package.__name__}"
        )
        return pkgutil.get_data(package.__package__, filename).decode("utf-8")
    else:
        dirname = dirname or "."
        logger.debug(f"loading file {filename} from {dirname}")
        with open(f"{dirname}/{filename}") as f:
            return f.read()

def raise_error_if_none(thing):
    if thing is None:
        # would be nice if we could include context
        raise ValueError("should not be None")
    return thing

# TODO: maybe an Environment will give better error messages
# wit filename and linenumber
#jinja2_env = jinja2.Environment(finalize=my_finalize)

def load_jinja_data(file_loc: FileLocation, vars: Mapping):
    global _current_jinja_file
    # we remember the file that jinja is parsing for better error messages
    # Not sure if there is a better way to do this currently
    _current_jinja_file = file_loc.filename
    filedata = load_data(file_loc=file_loc)
    tmpl = jinja2.Template(
        filedata,
        undefined=jinja2.StrictUndefined,
        finalize=raise_error_if_none,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    result = tmpl.render(vars)
    _current_jinja_file = None
    return result


def load_yaml(file_loc: FileLocation) -> Mapping:
    return yaml_parser.load(load_data(file_loc=file_loc))


def load_jinyaml(file_loc: FileLocation, vars: Mapping) -> Mapping:
    return yaml_parser.load(load_jinja_data(file_loc=file_loc, vars=vars))


def yaml_parse(data, loc: FileLocation = None):
    try:
        return yaml_parser.load(data)
    except:
        logger.error(f"Error parsing {loc or ''}\n" + data)
        raise


def yaml_dump(data, file):
    yaml_parser.dump(data, file)
