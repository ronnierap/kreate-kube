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
            loader=RepoLoader(konfig),
        )
        self.env.globals["konf"] = konfig.yaml # this might be deprecated in future
        self.env.globals["konfig"] = konfig
        self.yaml_parser = YAML()
        self.add_jinja_filter("b64encode", b64encode)
        self.add_jinja_filter("handle_empty_str", handle_empty_str)

    def add_jinja_filter(self, name, func):
        self.env.filters[name] = func

    def render_jinja(self, filename: str, vars: Mapping) -> str:
        tmpl = self.env.get_template(filename)
        try:
            return tmpl.render(vars)
        except jinja2.exceptions.TemplateSyntaxError as e:
            logger.error(
                f"Syntax Error in jinja2 template {e.filename}:{e.lineno} {e.message}"
            )
            raise
        except TypeError:
            raise ValueError(f"Problem loading jinja template {filename}")
        except jinja2.exceptions.TemplateError as e:
            found = False
            for line in traceback.format_exc().splitlines():
                if "in top-level template code" in line:
                    found = True
                    logger.error(f"Error in {line.strip()}, {e}")
            if not found:
                logger.error(f"Error when rendering {filename}, {e}")
            raise
        except Exception as e:
            logger.error(f"ERROR when parsing {filename}")
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
        logger.debug("empty value to b64encode")
        return ""


def handle_empty_str(value: str) -> str:
    if value == "":
        return '""'
    return value


class RepoLoader(jinja2.BaseLoader):
    def __init__(self, konfig):
        self.konfig = konfig

    def get_source(self, environment, filename):
        data = self.konfig.load_repo_file(filename)
        if isinstance(data, bytes):
            data = data.decode()
        return data, filename, lambda: True
