import os
import logging
import shutil
import inspect
from typing import Mapping, List, TYPE_CHECKING
from pathlib import Path
from ._core import wrap
from ._konfig import Konfig
from ._kontext import load_class
from ._komp import Komponent, KomponentKlass, TextFile, JinjaFile

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
        self.komponents: List[Komponent] = []
        self.komponents_by_id = {}
        self.klasses: Mapping[str, KomponentKlass] = {}
        self.strukture = wrap(konfig.get_path("strukt"))
        self.target_path = Path(konfig.get_path("system.target_dir", f"build"))
        for mod in self.kontext.modules:
            mod.init_app(self)
        self.register_klasses()

    def kreate_komponents(self):
        self.kreate_komponents_from_strukture()
        for mod in self.kontext.modules:
            mod.kreate_app_komponents(self)

    def komponent_naming(self, klass_name: str, shortname: str) -> str:
        formatstr = None
        naming = self.konfig.get_path(f"system.template.{klass_name}.naming")
        if isinstance(naming, Mapping):
            if shortname in naming:
                formatstr = naming[shortname]
            elif "*" in naming:
                formatstr = naming["*"]
        elif isinstance(naming, str):
            formatstr = naming
        elif naming is not None:
            raise ValueError(
                f"Unsupported naming for {klass_name}.{shortname}: {naming}"
            )
        if formatstr:
            return formatstr.format(
                shortname=shortname,
                appname=self.konfig.get_path("app.appname"),
            )
        return None

    def add_komponent(self, komp: "Komponent") -> None:
        if komp.skip():
            return
        self.komponents.append(komp)
        self.komponents_by_id[komp.id] = komp

    def aktivate_komponents(self):
        for komp in self.komponents:
            logger.debug(f"aktivating {komp.id}")
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
                logger.info(f"skipping file for {komp.id}")

    def kreate_komponents_from_strukture(self):
        if not self.strukture:
            raise ValueError("no strukture found in konfig")
        for klass_name in sorted(self.strukture.keys()):
            if klass_name in self.klasses:
                strukt = self.strukture.get(klass_name, None)
                strukt = strukt or {"main": {}}
                for shortname in sorted(strukt.keys()):
                    logger.debug(f"kreating komponent {klass_name}.{shortname}")
                    self.kreate_komponent(klass_name, shortname)
            elif klass_name != "default" and klass_name != "use":
                raise ValueError    (f"Unknown toplevel komponent {klass_name}")

    ####################################################

    def register_klass(self, python_class, name: str = None, info: Mapping = None):
        name = name or python_class.__name__
        info = info or {}
        self.klasses[name] = KomponentKlass(python_class, name, info)

    def register_klasses(self):
        self.register_klass(TextFile)
        self.register_klass(JinjaFile)
        templates = dict(
            self.konfig.get_path("system.template", {})
        )  # TODO: deprecated after 2.0
        templates.update(self.konfig.get_path("system.klasses", {}))
        for klass_name, info in templates.items():
            logger.debug(f"adding klass {klass_name}")
            if clsname := info.get("class"):
                cls = load_class(clsname)
                self.register_klass(cls, klass_name, info)
            else:
                raise KeyError(f"No python class defined for Klass {klass_name}")

    def kreate_komponent(self, klass_name: str, shortname: str = None):
        if kls := self.klasses[klass_name]:
            return kls.kreate_komponent(app=self, shortname=shortname)
        else:
            raise ValueError(f"Unknown klass name {klass_name}")
