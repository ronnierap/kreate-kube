import logging
import os
import jinja2

from collections.abc import Mapping
from typing import Any

from ._core import wrap
from ._app import App

logger = logging.getLogger(__name__)


class Komponent:
    """A base class for other komponents"""

    def __init__(
        self,
        app: App,
        shortname: str = None,
        kind: str = None,
    ):
        self.app = app
        self.kind = kind or self.__class__.__name__
        self.shortname = shortname or "main"
        self.strukture = wrap(self._find_strukture())
        self.field = Field(self)
        name = (
            self.strukture.get("name", None)
            or app.komponent_naming(self.kind, self.shortname)
            or self.calc_name()
        )
        self.name = name.lower()
        if self.skip():
            # do not load the template (strukture might be missing)
            logger.info(f"ignoring {self.name}")
        else:
            logger.debug(f"adding  {self.kind}.{self.shortname}")
            self.app.add_komponent(self)


    def skip(self):
        return self.strukture.get("ignore", False)

    def aktivate(self):
        pass

    def __str__(self):
        return f"<Komponent {self.kind}.{self.shortname} {self.name}>"

    def calc_name(self):
        if self.shortname == "main":
            return f"{self.app.appname}-{self.kind}"
        return f"{self.app.appname}-{self.kind}-{self.shortname}"

    def _find_strukture(self):
        typename = self.kind
        strukt = self.app.strukture if self.app else {}
        if typename in strukt and self.shortname in strukt[typename]:
            logger.debug(f"using named strukture {typename}.{self.shortname}")
            return self.app.strukture[typename][self.shortname]
        logger.debug(f"could not find strukture for {typename}.{self.shortname}")
        return {}

    def kreate_file(self) -> None:
        raise NotImplementedError(f"no kreate_file for {type(self)}")

    def invoke_options(self):
        options = self.strukture.get("options", [])
        for opt in options or []:
            if isinstance(opt, str):
                logger.debug(f"invoking {self} option {opt}")
                getattr(self, opt)()
            elif isinstance(opt, Mapping):
                for key in opt.keys():
                    val = opt.get(key)
                    if isinstance(val, Mapping):
                        logger.debug(
                            f"invoking {self} option {key}"
                            f" with kwargs parameters {val}"
                        )
                        getattr(self, key)(**dict(val))
                    elif isinstance(val, list):
                        logger.debug(
                            f"invoking {self} option {key}"
                            f" with list parameters {val}"
                        )
                        getattr(self, key)(*val)
                    elif isinstance(val, str):
                        logger.debug(
                            f"invoking {self} option {key}"
                            f" with string parameter {val}"
                        )
                        getattr(self, key)(val)
                    elif isinstance(val, int):
                        logger.debug(
                            f"invoking {self} option {key}" f" with int parameter {val}"
                        )
                        getattr(self, key)(int(val))
                    else:
                        logger.warning(f"option map {opt} for {self.name} not supported")

            else:
                logger.warning(f"option {opt} for {self.name} not supported")

    def get_filename(self):
        if self.strukture.get("target_filename"):
            return self.strukture.get("target_filename")
        return f"{self.kind.lower()}-{self.shortname}.yaml"

    def _field(self, fieldname: str, default=None):
        if fieldname in self.strukture:
            return self.strukture[fieldname]
        konf = self.app.konfig
        result = konf.get_path(f"val.{self.kind}.{self.shortname}.{fieldname}")
        if result is None:
            result = konf.get_path(f"val.{self.kind}.{fieldname}")
        if result is None:
            result = konf.get_path(f"val.generic.{fieldname}")
        if result is not None:
            return result
        if default is not None:
            return default
        raise jinja2.exceptions.UndefinedError(f"Unknown field {fieldname} in {self}")

    def _contains_field(self, key) -> bool:
        marker = object()
        if self._field(key, marker) is marker:
            return False
        return True


class Field:
    def __init__(self, komp: Komponent) -> None:
        self._komp = komp

    def __getattr__(self, __name: str) -> Any:
        return self._komp._field(__name)

    def __contains__(self, key):
        return self._komp._contains_field(key)


class JinjaKomponent(Komponent):
    """An object that is parsed from a jinja template and strukture"""

    def __init__(self, app: App, shortname: str = None, kind: str = None):
        if kind is None:
            kind = self.__class__.__name__
        if shortname is None:
            shortname = "main"
        super().__init__(app, shortname, kind)
        self.template = self.app.kind_templates[self.kind]

    def aktivate(self):
        vars = self._template_vars()
        self.data = self.app.konfig.jinyaml.render_jinja(self.template, vars)

    def is_secret(self) -> bool:
        return False

    def kreate_file(self) -> None:
        filename = self.get_filename()
        if filename:
            path = self.app.target_path / filename
            if self.is_secret():
                self.app.kontext.add_cleanup_path(path)
            os.makedirs(path.parent, exist_ok=True)
            with open(path, "w") as f:
                f.write(self.data)

    def _template_vars(self):
        return {
            "strukt": self.strukture,
            "app": self.app.konfig.get_path("app", {}),
            "my": self,
        }


class JinYamlKomponent(JinjaKomponent):
    def aktivate(self):
        vars = self._template_vars()
        self.yaml = wrap(self.app.konfig.jinyaml.render(self.template, vars))
        self.invoke_options()
        self.add_additions()
        self.remove_deletions()

    def get_path(self, path: str, default=None):
        return self.yaml._get_path(path, default=default)

    def set_path(self, path: str, val):
        return self.yaml._set_path(path, val)

    def kreate_file(self) -> None:
        filename = self.get_filename()
        if filename:
            path = self.app.target_path / filename
            if self.is_secret():
                self.app.kontext.add_cleanup_path(path)
            os.makedirs(path.parent, exist_ok=True)
            with open(path, "w") as f:
                self.app.konfig.jinyaml.dump(self.yaml.data, f)

    def add_additions(self):
        additions = self.strukture.get("add", {})
        for path in additions:
            self.yaml._set_path(path, additions[path])

    def remove_deletions(self):
        removals = self.strukture.get("remove", [])
        for path in removals:
            self.yaml._del_path(path)

    def optional(self, fieldname: str) -> str:
        if fieldname not in self.field:
            return ""
        val = self._field(fieldname)
        return f"{fieldname}: {val}"
