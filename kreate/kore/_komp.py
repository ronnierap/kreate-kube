import logging
from collections.abc import Mapping
import os
from typing import Any

from ._core import DeepChain, wrap
from ._jinyaml import FileLocation, yaml_dump, yaml_parse, load_jinja_data
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
        self.strukture = self._calc_strukture()
        self.skip = self.strukture.get("ignore", False)
        self.field = Field(self)
        name = (self.strukture.get("name", None)
            or app.komponent_naming_convention(self.kind, self.shortname)
            or self.calc_name()
        )
        self.name = name.lower()
        if self.skip:
            # do not load the template (strukture might be missing)
            logger.info(f"ignoring {self.name}")
        else:
            logger.debug(f"adding  {self.kind}.{self.shortname}")
        if not self.app:
            raise ValueError("Komponent {self.name} has no application")
        self.app.add(self)

    def aktivate(self):
        pass

    def __str__(self):
        return f"<Komponent {self.kind}.{self.shortname} {self.name}>"

    def calc_name(self):
        if self.shortname == "main":
            return f"{self.app.appname}-{self.kind}"
        return f"{self.app.appname}-{self.kind}-{self.shortname}"

    def _calc_strukture(self):
        strukt = self._find_strukture()
        defaults = self._find_defaults()
        return DeepChain(
            strukt,
            {"default": defaults},
            {"default": self._find_generic_defaults()},
        )

    def _find_defaults(self):
        strukt = self.app.strukture if self.app else {}
        if self.kind in strukt.get("default", {}):
            logger.debug(f"using defaults for {self.kind}")
            return self.app.strukture.default[self.kind]
        return {}

    def _find_generic_defaults(self):
        strukt = self.app.strukture if self.app else {}
        if "generic" in strukt.get("default", {}):
            logger.debug("using generic defaults")
            return self.app.strukture.default["generic"]
        return {}

    def _find_strukture(self):
        typename = self.kind
        strukt = self.app.strukture if self.app else {}
        if typename in strukt and self.shortname in strukt[typename]:
            logger.debug(f"using named strukture {typename}.{self.shortname}")
            return self.app.strukture[typename][self.shortname]
        logger.debug(
            f"could not find strukture for {typename}.{self.shortname}"
        )
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
                            f"invoking {self} option {key}"
                            f" with int parameter {val}"
                        )
                        getattr(self, key)(int(val))
                    else:
                        logger.warn(
                            f"option map {opt} for {self.name} not supported"
                        )

            else:
                logger.warn(f"option {opt} for {self.name} not supported")

    @property
    def dirname(self):
        return None

    @property
    def filename(self):
        return f"{self.kind.lower()}-{self.shortname}.yaml"

    def _field(self, fieldname: str, default=None):
        if fieldname in self.strukture:
            return self.strukture[fieldname]
        if (self.shortname in self.app.konfig.values
            and fieldname in self.app.konfig.values[self.shortname]
        ):
            return self.app.konfig.values[self.shortname][fieldname]
        if fieldname in self.app.konfig.values:
            return self.app.konfig.values[fieldname]
        if fieldname in self.strukture.get("default", {}):
            return self.strukture["default"][fieldname]
        # The following might not be needed using Deepchain anyway
        if fieldname in self.strukture.get("default", {}).get("generic",{}):
            return self.strukture["default"]["generic"][fieldname]
        if default is not None:
            return default
        raise ValueError(f"Unknown field {fieldname} in {self}")


class Field:
    def __init__(self, komp: Komponent) -> None:
        self._komp = komp

    def __getattr__(self, __name: str) -> Any:
        return self._komp._field(__name)



class JinjaKomponent(Komponent):
    """An object that is parsed from a jinja template and strukture"""

    def __init__(
        self,
        app: App,
        shortname: str = None,
        kind: str = None,
        template: FileLocation = None,
    ):
        super().__init__(app, shortname, kind)
        template = template or self.app.kind_templates[self.kind]
        self.template = template

    def aktivate(self):
        vars = self._template_vars()
        self.data = load_jinja_data(self.template, vars)
        self.invoke_options()

    def kreate_file(self) -> None:
        filename = self.filename
        if filename:
            if self.dirname:
                dir = f"{self.app.konfig.target_dir}/{self.dirname}"
            else:
                dir = self.app.konfig.target_dir
            os.makedirs(dir, exist_ok=True)
            with open(f"{dir}/{filename}", "wb") as f:
                f.write(self.data)

    def _template_vars(self):
        return {
            "strukt": self.strukture,
            "default": self.strukture.default,
            "app": self.app,
            "my": self,
            "val": self.app.konfig.values,
            "var": self.app.konfig.values.get("vars", {}),
            "secret": self.app.konfig.secrets,
            "function": self.app.konfig.functions,
        }


class JinYamlKomponent(JinjaKomponent):
    def aktivate(self):
        vars = self._template_vars()
        self.data = load_jinja_data(self.template, vars)
        self.yaml = wrap(yaml_parse(self.data, self.template))
        self.invoke_options()
        self.add_additions()
        self.remove_deletions()

    def kreate_file(self) -> None:
        filename = self.filename
        if filename:
            if self.dirname:
                dir = f"{self.app.konfig.target_dir}/{self.dirname}"
            else:
                dir = self.app.konfig.target_dir
            os.makedirs(dir, exist_ok=True)
            with open(f"{dir}/{filename}", "wb") as f:
                yaml_dump(self.yaml.data, f)

    def add_additions(self):
        additions = self.strukture.get("add", {})
        for path in additions:
            self.yaml._set_path(path, additions[path])

    def remove_deletions(self):
        removals = self.strukture.get("remove", [])
        for path in removals:
            self.yaml._del_path(path)
