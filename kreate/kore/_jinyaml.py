import jinja2
import logging
import base64
import traceback
from sys import exc_info
from collections.abc import Mapping
from ruamel.yaml import YAML

logger = logging.getLogger(__name__)


class JinYaml:
    def __init__(self, konfig) -> None:
        self.konfig = konfig
        self.env = jinja2.Environment(
            undefined=jinja2.StrictUndefined,
            finalize=raise_error_if_none,
            trim_blocks=True,
            lstrip_blocks=True,
            loader=RepoLoader(konfig)
        )
        self.env.globals["konf"] = konfig
        self.yaml_parser = YAML()
        self.add_jinja_filter("b64encode", b64encode)

    def add_jinja_filter(self, name, func):
        self.env.filters[name] = func

    def render_jinja(self, filename: str, vars: Mapping) -> str:
        tmpl = self.env.get_template(filename)
        try:
            return tmpl.render(vars)
        except:
            logger.error(f"Error when rendering {filename}")
            raise

    def render(self, fname: str, vars: Mapping) -> Mapping:
        text = self.render_jinja(fname, vars)
        try:
            return self.yaml_parser.load(text)
        except:
            logger.error(f"Error parsing {fname}\n" + text)
            raise

    def dump(self, data, output_file):
        self.yaml_parser.dump(data, output_file)


def raise_error_if_none(thing):
    if thing is None:
        # would be nice if we could include context
        raise ValueError("should not be None")
    return thing


def b64encode(value: str) -> str:
    if value:
        if isinstance(value, bytes):
            res = base64.b64encode(value)
        else:
            res = base64.b64encode(value.encode())
        return res.decode()
    else:
        logger.warning("empty value to b64encode")
        return ""


def jinja2_template_error_lineno():
    for line in traceback.format_exc().splitlines():
        if 'File "<template>"' in line:
            print(line)
    type, value, tb = exc_info()
    if not issubclass(type, jinja2.TemplateError):
        return None
    if hasattr(value, "lineno"):
        # in case of TemplateSyntaxError
        return value.lineno
    while tb:
        # print(tb.tb_frame.f_code.co_filename, tb.tb_lineno)
        if tb.tb_frame.f_code.co_filename == "<template>":
            return tb.tb_lineno
        tb = tb.tb_next


class RepoLoader(jinja2.BaseLoader):
    def __init__(self, konfig):
        self.konfig = konfig

    def get_source(self, environment, filename):
        data = self.konfig.load_repo_file(filename)
        if isinstance(data, bytes):
            data = data.decode()
        return data, filename, lambda: True
