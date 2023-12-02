import os
import logging
import shutil
import inspect
from typing import Mapping, List, TYPE_CHECKING
from pathlib import Path
from ._core import wrap
from ._konfig import Konfig
from ._kontext import load_class
from ._komp import Komponent, KomponentKlass

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
        self.komponents: List[Komponent] = []
        self.klasses: Mapping[KomponentKlass] = {}
        self.strukture = wrap(konfig.get_path("strukt"))
        self.target_path = Path(konfig.get_path("system.target_dir", f"build/{self.appname}-{self.env}"))
        for mod in self.kontext.modules:
            mod.init_app(self)
        self.register_klasses_from_konfig()

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
            raise ValueError(f"Unsupported naming for {klass_name}.{shortname}: {naming}")
        if formatstr:
            return formatstr.format(
                kind=klass_name,
                shortname=shortname,
                appname=self.appname,
            )
        return None

    def add_komponent(self, komp: "Komponent") -> None:
        if komp.skip():
            return
        self.komponents.append(komp)

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
            if kind in self.klasses:
                strukt = self.strukture.get(kind, None)
                strukt = strukt or {"main": {}}
                for shortname in sorted(strukt.keys()):
                    logger.debug(f"kreating komponent {kind}.{shortname}")
                    self.kreate_komponent(kind, shortname)
            elif kind != "default" and kind != "use":
                logger.warning(f"Unknown toplevel komponent {kind}")

####################################################

    def register_klasses_from_konfig(self):
        templates = self.konfig.get_path("system.template", {})
        for klass_name, info in templates.items():
            logger.debug(f"adding klass {klass_name}")
            if clsname := info.get("class"):
                cls = load_class(clsname)
                self.klasses[klass_name] = KomponentKlass(cls, klass_name, info)
            else:
                raise KeyError(f"No python class defined for Klass {klass_name}")

    def kreate_komponent(self, klass_name: str, shortname: str = None):
        if kls := self.klasses[klass_name]:
            return kls.kreate_komponent(app=self, shortname=shortname)
        else:
            raise ValueError(f"Unknown klass name {klass_name}")
