import os
import logging
from typing import List, Set
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
        self.strukture = wrap(konfig.yaml.get("strukt"))
        self.target_dir = self.konfig.yaml.get("system", {}).get(
            "target_dir", "build"
        )
        self.target_path = Path(self.target_dir)

    def komponent_naming(self, kind: str, shortname: str) -> str:
        naming = self.konfig.yaml.get("system", {}).get("naming", {})
        formatstr: str = naming.get(kind, None)
        if formatstr:
            return formatstr.format(
                kind=kind, shortname=shortname, appname=self.appname
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
        raise NotImplementedError(
            f"can not create komponent for {kind}.{shortname}"
        )

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
        os.makedirs(self.target_dir, exist_ok=True)
        for komp in self.komponents:
            if komp.filename:
                if komp.dirname:
                    logger.info(
                        f"kreating file {komp.dirname}/{komp.filename}"
                    )
                else:
                    logger.info(f"kreating file {komp.filename}")
                komp.kreate_file()
            else:
                logger.info(f"skipping file for {komp.kind}.{komp.shortname}")

    def kreate_komponents_from_strukture(self):
        for kind in sorted(self.strukture.keys()):
            if kind in self.kind_classes:
                strukt = self.strukture.get(kind, None)
                strukt = strukt or {"main": {}}
                for shortname in sorted(strukt.keys()):
                    logger.debug(f"kreating komponent {kind}.{shortname}")
                    self.kreate_komponent(kind, shortname)
            elif kind != "default" and kind != "use":
                logger.warning(f"Unknown toplevel komponent {kind}")
