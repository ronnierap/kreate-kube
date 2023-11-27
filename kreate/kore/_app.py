import os
import logging
import shutil
import inspect
from typing import Mapping, List, TYPE_CHECKING
from pathlib import Path
from ._core import wrap
from ._konfig import Konfig
from ._kontext import load_class
if TYPE_CHECKING:
    from ._komp import Komponent

logger = logging.getLogger(__name__)


class App:
    """
    An App is a container of komponents
    These components are kreated from a strukture file, but may also
    be kreated manually in a script using the kreate_komponent method.

    The general flow is as follows:
      app = SomeApp(konfig)   # loads the strukture from the konfig
      app.kreate_komponents() # from_strukture or from script
      app.tune_komponents()   # render the templates for each komponent
      app.kreate_file()       # write the rendered template to a file
    """

    def __init__(self, konfig: Konfig):
        self.konfig = konfig
        self.kontext = konfig.kontext
        self.appname = konfig.get_path("app.appname")
        self.env = konfig.get_path("app.env")
        self.komponents: List["Komponent"] = []
        self._kinds = {}
        self.kind_templates = {}
        self.kind_classes = {}
        self.strukture = wrap(konfig.get_path("strukt"))
        self.target_path = Path(konfig.get_path("system.target_dir", f"build/{self.appname}-{self.env}"))
        for mod in self.kontext.modules:
            mod.init_app(self)
        self.register_templates_from_konfig()

    def kreate_komponents(self):
        self.kreate_komponents_from_strukture()
        for mod in self.kontext.modules:
            mod.kreate_app_komponents(self)

    def komponent_naming(self, kind: str, shortname: str) -> str:
        formatstr = None
        naming = self.konfig.get_path(f"system.template.{kind}.naming")
        if isinstance(naming, Mapping):
            if shortname in naming:
                formatstr = naming[shortname]
            elif "*" in naming:
                formatstr = naming["*"]
        elif isinstance(naming, str):
            formatstr = naming
        elif naming is not None:
            raise ValueError(f"Unsupported naming for {kind}.{shortname}: {naming}")
        # TODO: remove next 2 lines in 1.0.0, backward compatible with 0.9.*
        if not formatstr:
            formatstr = self.konfig.get_path(f"system.naming.{kind}")
        if formatstr:
            return formatstr.format(
                kind=kind,
                shortname=shortname,
                appname=self.appname,
            )
        return None

    def add_komponent(self, komp: "Komponent") -> None:
        if komp.skip():
            return
        self.komponents.append(komp)
        map = self._kinds.get(komp.kind.lower(), None)
        if map is None:
            map = wrap({})
            self._kinds[komp.kind.lower()] = map
        map[komp.shortname] = komp

    def aktivate_komponents(self):
        for komp in self.komponents:
            logger.debug(f"aktivating {komp.kind}.{komp.shortname}")
            komp.aktivate()

    def kreate_files(self):
        if self.target_path.exists():
            logger.info(f"removing target directory {self.target_path}")
            shutil.rmtree(self.target_path)
        os.makedirs(self.target_path, exist_ok=True)
        self.aktivate_komponents()
        for komp in self.komponents:
            if komp.get_filename():
                logger.info(f"kreating file {komp.get_filename()}")
                komp.kreate_file()
            else:
                logger.info(f"skipping file for {komp.kind}.{komp.shortname}")

    def kreate_komponents_from_strukture(self):
        if not self.strukture:
            raise ValueError("no strukture found in konfig")
        for kind in sorted(self.strukture.keys()):
            if kind in self.kind_classes:
                strukt = self.strukture.get(kind, None)
                strukt = strukt or {"main": {}}
                for shortname in sorted(strukt.keys()):
                    logger.debug(f"kreating komponent {kind}.{shortname}")
                    self.kreate_komponent(kind, shortname)
            elif kind != "default" and kind != "use":
                logger.warning(f"Unknown toplevel komponent {kind}")

####################################################

    def register_templates_from_konfig(self):
        templates = self.konfig.get_path("system.template", {})
        for key, _def in templates.items():
            logger.debug(f"adding custom template {key}")
            if _def.get("template"):
                if _def.get("class"):
                    self.register_template_path(key, _def["class"], _def["template"])
                else:
                    self.kind_templates = _def["template"]

    def register_template_path(self, kind: str, clsname: str, path: str) -> None:
        self.kind_templates[kind] = path
        self.kind_classes[kind] = load_class(clsname)

    def register_template(self, kind: str, cls, filename=None, package=None):
        if kind in self.kind_templates:
            if cls is None:
                cls = self.kind_classes[kind]
                logger.debug(
                    f"overriding template {kind} "
                    f"using existing class {cls.__name__}"
                )
            else:
                logger.debug(f"overriding template {kind} using default class")
        filename = filename or f"{kind}.yaml"
        if package:
            filename = f"py:{package.__name__}:{filename}"
        logger.debug(f"registering template {kind}: {filename}")
        if cls is None:
            raise ValueError(f"No class specified for template {kind}: {filename}")
        self.kind_templates[kind] = filename
        self.kind_classes[kind] = cls

    def register_template_class(self: str, cls, filename=None, package=None):
        kind = cls.__name__
        self.register_template(kind, cls, filename=filename, package=package)

    def register_template_file(self, kind: str, cls=None, filename=None, package=None):
        self.register_template(kind, cls, filename=filename, package=package)

    def kreate_komponent(self, kind: str, shortname: str = None):
        cls = self.kind_classes[kind]
        if inspect.isclass(cls):
            return cls(app=self, kind=kind, shortname=shortname)
        else:
            raise ValueError(f"Unknown template type {type(cls)}, {cls}")
