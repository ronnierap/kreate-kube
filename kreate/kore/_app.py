import os
import logging
import shutil
from typing import Mapping
from pathlib import Path

from ._core import wrap, deep_update
from ._konfig import Konfig

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
        self.appname = konfig.get_path("app.appname")
        self.env = konfig.get_path("app.env")
        self.konfig = konfig
        self.komponents = []
        self._kinds = {}
        self.strukture = wrap(konfig.get_path("strukt"))
        self.target_path = Path(konfig.get_path("system.target_dir", f"build/{self.appname}-{self.env}"))

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

    def add_komponent(self, komp) -> None:
        if not komp.skip:
            self.komponents.append(komp)
        map = self._kinds.get(komp.kind.lower(), None)
        if map is None:
            map = wrap({})
            self._kinds[komp.kind.lower()] = map
        map[komp.shortname] = komp

    def __getattr__(self, attr):
        if attr in self.__dict__ or attr == "_dict":
            return super().__getattribute__(attr)
        return self._kinds.get(attr, None)

    def kreate_komponent(self, kind: str, shortname: str = None):
        raise NotImplementedError(f"can not create komponent for {kind}.{shortname}")

    def kreate_komponents(self):
        self.kreate_komponents_from_strukture()

    def tune_komponents(self):
        pass

    def aktivate_komponents(self):
        for komp in self.komponents:
            logger.debug(f"aktivating {komp.kind}.{komp.shortname}")
            komp.aktivate()
        self.tune_komponents()

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
