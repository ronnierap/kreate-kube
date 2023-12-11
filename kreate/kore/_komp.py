import logging
import os
import re
from collections.abc import Mapping
from typing import Any, TYPE_CHECKING, Sequence
import jinja2

from ._core import wrap, DictWrapper
from ._konfig import Konfig
from ._kontext import check_requires

if TYPE_CHECKING:
    from ._app import App

logger = logging.getLogger(__name__)


class KomponentKlass:
    def __init__(self, python_class, name: str, info: Mapping) -> None:
        self.python_class = python_class
        self.name = name
        self.info : DictWrapper = wrap(info)
        self._req_check = None

    def kreate_komponent(self, app: "App", shortname: str) -> "Komponent":
        return self.python_class(app, self, shortname)

    def check_requirements(self) -> bool:
        if self._req_check is None:
            self._req_check = check_requires(self.info.get("requires", {}),
                msg=f"{self.name}: "
            )
        return self._req_check

    def __str__(self) -> str:
        return f"<KomponentKlass {self.name}>"

class Komponent:
    """A base class for other komponents"""

    def __init__(
            self,
            app: "App",
            klass: KomponentKlass,
            shortname: str = None,
    ):
        self.app = app
        self.klass = klass
        klass.check_requirements()
        self.shortname = shortname or "main"
        self.id = f"{klass.name}.{shortname}"
        self.strukture = wrap(self._find_strukture())
        self.field = Field(self)
        name = (
                self.strukture.get("name", None)
                or app.komponent_naming(self.klass.name, self.shortname)
                or self.calc_name()
        )
        self.name = name.lower()
        if self.skip():
            # do not load the template (strukture might be missing)
            logger.info(f"ignoring {self.name}")
        else:
            logger.debug(f"adding  {self.id}")
            self.app.add_komponent(self)

    def skip(self):
        return self.strukture.get("ignore", False)

    def implements(self, name: str) -> bool:
        if self.klass.info.get_path(f"implements.{name}", "True") == "True":
            return True
        for cls in self.__class__.__mro__:
            if cls.__name__ == name:
                return True
        return False

    def aktivate(self):
        # Abstract Method, sub-classes may implement this method
        pass

    def __str__(self) -> str:
        return f"<{self.__class__.__name__} {self.id} {self.name}>"

    def calc_name(self):
        appname = self.app.konfig.get_path("app.appname")
        if self.shortname == "main":
            return f"{appname}-{self.klass.name}"
        return f"{appname}-{self.klass.name}-{self.shortname}"

    def _find_strukture(self):
        strukt = self.app.strukture.get_path(self.id)
        if strukt is None:
            logger.debug(f"could not find strukture for {self.id}")
            return {}
        return strukt

    def is_secret(self) -> bool:
        return self.klass.info.get("secret", False)

    def kreate_file(self) -> None:
        filename = self.get_filename()
        if filename:
            path = self.app.target_path / filename
            if self.is_secret():
                self.app.kontext.add_cleanup_path(path)
            os.makedirs(path.parent, exist_ok=True)
            text = self.kreate_file_data()
            with open(path, "w") as f:
                f.write(text)

    def kreate_file_data(self) -> str:
        raise NotImplementedError(f"no kreate_file_data for {type(self)}")

    def invoke_options(self):
        options = self.strukture.get("options", [])
        for opt in options or []:
            if isinstance(opt, str):
                logger.debug(f"invoking {self} option {opt}")
                getattr(self, opt)()
            elif isinstance(opt, Mapping):
                self.__invoke_mapping_options(opt)
            else:
                logger.warning(f"option {opt} for {self.name} not supported")

    def __invoke_mapping_options(self, opt):
        for key in opt.keys():
            val = opt.get(key)
            if isinstance(val, Mapping):
                logger.debug(
                    f"invoking {self} option {key}" f" with kwargs parameters {val}"
                )
                getattr(self, key)(**dict(val))
            elif isinstance(val, list):
                logger.debug(
                    f"invoking {self} option {key}" f" with list parameters {val}"
                )
                getattr(self, key)(*val)
            elif isinstance(val, str):
                logger.debug(
                    f"invoking {self} option {key}" f" with string parameter {val}"
                )
                getattr(self, key)(val)
            elif isinstance(val, int):
                logger.debug(f"invoking {self} option {key} with int parameter {val}")
                getattr(self, key)(int(val))
            else:
                logger.warning(f"option map {opt} for {self.name} not supported")

    def get_filename(self):
        if self.strukture.get("target_filename"):
            return self.strukture.get("target_filename")
        return f"{self.klass.name}-{self.shortname}.yaml".lower()

    def _field(self, fieldname: str, default=None):
        if fieldname in self.strukture:
            return self.strukture[fieldname]
        if result := self.strukture.get_path(f"field.{fieldname}"):
            return result
        konf = self.app.konfig
        result = konf.get_path(f"val.{self.id}.{fieldname}")  # deprecated in 2.0.0
        if result is None:
            result = konf.get_path(f"val.field.{self.id}.{fieldname}")
        if result is None:
            result = konf.get_path(
                f"val.{self.klass.name}.{fieldname}"
            )  # deprecated in 2.0.0
        if result is None:
            result = konf.get_path(f"val.field.{self.klass.name}.{fieldname}")
        if result is None:
            result = konf.get_path(f"val.generic.{fieldname}")  # deprecated in 2.0.0
        if result is None:
            result = konf.get_path(f"val.field.generic.{fieldname}")
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

    def get(self, __name: str) -> Any:
        return self._komp._field(__name)

    def __getattr__(self, __name: str) -> Any:
        return self._komp._field(__name)

    def __contains__(self, key):
        return self._komp._contains_field(key)


class TextFile(Komponent):
    def __init__(self, app: "App", klass: KomponentKlass, shortname: str = None):
        super().__init__(app, klass, shortname)
        self.from_location = self.strukture.get("from")
        self.filename = self.strukture.get("filename")

    def get_filename(self):
        return self.filename

    def is_secret(self):
        return super().is_secret() or "dekrypt:" in self.from_location

    def kreate_file_data(self) -> str:
        return self.app.konfig.load_repo_file(self.from_location)


class JinjaKomponent(Komponent):
    """An object that is parsed from a jinja template and strukture"""

    def __init__(self, app: "App", klass: KomponentKlass, shortname: str = None):
        super().__init__(app, klass, shortname)
        self.data = None
        self._template_text = None

    # caching template content
    def template_text(self, konfig: Konfig):
        if not self._template_text:
            tmpl = self.get_template_location()
            self._template_text = konfig.load_repo_file(tmpl)
        return self._template_text

    def template_find_text(self, reg_exp: str) -> Sequence[str]:
        return re.findall(reg_exp, self.klass.template_text(self.app.konfig))

    def aktivate(self):
        komponent_vars = self._template_vars()
        template = self.get_template_location()
        if not template:
            raise KeyError(f"no template defined for {self.id} in {self.klass.info}")
        self.data = self.app.konfig.jinyaml.render_jinja(template, komponent_vars)

    def get_template_location(self) -> str:
        return self.klass.info.get("template")

    def kreate_file_data(self) -> None:
        return self.data

    def _template_vars(self):
        result = dict(self.app.konfig.yaml)
        result["my"] = self
        return result


class JinjaFile(JinjaKomponent):
    def get_template_location(self) -> str:
        return self.strukture.get("template")


class MultiJinYamlKomponent(JinjaKomponent):
    def __init__(self, app: "App", klass: KomponentKlass, shortname: str = None):
        super().__init__(app, klass, shortname)
        self.documents = None

    def aktivate(self):
        template_vars = self._template_vars()
        template = self.get_template_location()
        self.documents = self.app.konfig.jinyaml.render_multi_yaml(
            template, template_vars
        )

    def kreate_file(self) -> None:
        filename = self.get_filename()
        if filename:
            path = self.app.target_path / filename
            if self.is_secret():
                self.app.kontext.add_cleanup_path(path)
            os.makedirs(path.parent, exist_ok=True)
            with open(path, "w") as f:
                for doc in self.documents:
                    f.write("---\n")
                    self.app.konfig.jinyaml.dump(doc, f)


class JinYamlKomponent(JinjaKomponent):
    def __init__(self, app: "App", klass: KomponentKlass, shortname: str = None):
        super().__init__(app, klass, shortname)
        self.yaml = None

    def aktivate(self):
        template_vars = self._template_vars()
        template = self.get_template_location()
        self.yaml = wrap(self.app.konfig.jinyaml.render_yaml(template, template_vars))
        self.invoke_options()
        self.add_additions()
        self.remove_deletions()

    def get_path(self, path: str, default=None):
        return self.yaml.get_path(path, default=default)

    def set_path(self, path: str, val):
        return self.yaml.set_path(path, val)

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
            self.yaml.set_path(path, additions[path])

    def remove_deletions(self):
        removals = self.strukture.get("remove", [])
        for path in removals:
            self.yaml.del_path(path)

    def optional(self, fieldname: str) -> str:
        if fieldname not in self.field:
            return ""
        val = self._field(fieldname)
        if val:
            return f"{fieldname}: {val}"
        else:
            return ""
