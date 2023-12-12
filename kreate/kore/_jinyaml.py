import base64
import logging
import os
import re
import traceback
import warnings
from collections.abc import Mapping
from io import StringIO

import jinja2
from ruamel.yaml import YAML

logger = logging.getLogger(__name__)


def error(msg: str):
    # TODO: is this best Exception?
    raise RuntimeError(msg)


class JinYaml:
    def __init__(self, konfig) -> None:
        self.konfig = konfig
        self.env = jinja2.Environment(
            undefined=jinja2.StrictUndefined,
            finalize=raise_error_if_none,
            trim_blocks=True,
            lstrip_blocks=True,
            loader=RepoLoader(konfig),
            extensions=["jinja2.ext.debug"],
        )
        self.env.globals["konfig"] = konfig
        self.env.globals["jinja_extension"] = {
            "getenv": os.getenv,
            "sorted": sorted,
            "error": error,
            "warning": warnings.warn,
            "logger": logger,
        }
        self.yaml_parser = YAML()
        self.add_jinja_filter("b64encode", b64encode)
        self.add_jinja_filter("handle_empty_str", handle_empty_str)
        self.add_jinja_filter("yaml", self.yaml_filter)

    def yaml_filter(self, value, indent=""):
        if isinstance(value, str):
            return value
        if isinstance(value, int):
            return value
        out = StringIO()
        self.yaml_parser.dump(value, out)
        if isinstance(indent, int):
            start = "\n" + (" " * indent)
        else:
            start = "\n" + indent
        return start + start.join(out.getvalue().splitlines())

    def add_jinja_filter(self, name, func):
        self.env.filters[name] = func

    def render_jinja(self, filename: str, vars: Mapping) -> str:
        try:
            data = self.konfig.load_repo_file(filename)
            if data is None:
                logger.debug(f"did not find {filename}")
                return None
            tmpl = self.env.from_string(data)  # self.env.get_template(filename)
            return tmpl.render(vars)
        except jinja2.exceptions.TemplateSyntaxError as e:
            logger.error(
                f"Syntax Error in jinja2 template {e.filename}:{e.lineno} {e.message}"
            )
            raise
        except jinja2.exceptions.TemplateError as e:
            found = False
            for line in traceback.format_exc().splitlines():
                if "in top-level template code" in line:
                    found = True
                    logger.error(f"Error in {line.strip()}, {e}")
            if not found:
                logger.error(f"Error when rendering {filename}, {e}")
            raise

    def render_yaml(self, fname: str, vars: Mapping) -> Mapping:
        self.konfig.tracer.push(f"rendering jinja: {fname}")
        text = self.render_jinja(fname, vars)
        self.konfig.tracer.pop()
        if text is None:
            return None
        self.konfig.tracer.push(f"parsing yaml: {fname}\n" + text)
        result = self.yaml_parser.load(text)
        self.konfig.tracer.pop()
        return result

    def render_multi_yaml(self, fname: str, vars: Mapping) -> Mapping:
        self.konfig.tracer.push(f"rendering jinja: {fname}")
        text = self.render_jinja(fname, vars)
        self.konfig.tracer.pop()
        if text is None:
            return None
        self.konfig.tracer.push(f"parsing yaml: {fname}\n" + text)
        # Support to load multiple documents
        generator = self.yaml_parser.load_all(text)
        self.konfig.tracer.pop()
        return generator

    def dump(self, data, output_file):
        self.yaml_parser.dump(data, output_file)

    def load_with_jinja_includes(self, loc, lines):
        data : str = self.konfig.load_repo_file(loc)
        for line in data.splitlines():
            exp = r'^ *{% *include +[\'"](.*)[\'"] *%} *'
            if match := re.search(exp, line):
                inc_loc = match.group(1)
                logger.verbose(f"jinja including {inc_loc}")
                self.load_with_jinja_includes(inc_loc, lines)
            else:
                lines.append(line)


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
        if data is None:
            raise jinja2.TemplateNotFound(f"could not find template {filename}")
        if isinstance(data, bytes):
            data = data.decode()
        return data, filename, lambda: True
