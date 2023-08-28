import os
import logging

from ._core import DictWrapper
from ._konfig import Konfig

logger = logging.getLogger(__name__)


class App:
    def __init__(self, konfig: Konfig):
        self.appname = konfig.appname
        self.env = konfig.env
        self.konfig = konfig
        self.komponents = []
        self.komponent_naming_convention = self.komponent_naming
        self._kinds = {}
        self.aliases = {}
        self.strukture = konfig.calc_strukture()

    def komponent_naming(self, kind: str, shortname: str) -> str:
        return None

    def add_alias(self, kind: str, *aliases: str) -> None:
        if kind in self.aliases:
            self.aliases[kind].append(aliases)
        else:
            self.aliases[kind] = list(aliases)

    def get_aliases(self, kind: str):
        result = [kind, kind.lower()]
        if kind in self.aliases:
            result.append(*self.aliases[kind])
        return result

    def add(self, res) -> None:
        if not res.skip:
            self.komponents.append(res)
        map = self._kinds.get(res.kind, None)
        if map is None:
            map = DictWrapper({})
            self.get_aliases(res.kind)
            for alias in self.get_aliases(res.kind):
                self._kinds[alias] = map

        map[res.shortname] = res

    def __getattr__(self, attr):
        if attr in self.__dict__ or attr == "_dict":
            return super().__getattribute__(attr)
        return self._kinds.get(attr, None)

    def kreate_komponent(self, kind: str, shortname: str = None):
        raise NotImplementedError(
            f"can not create komponent for {kind}.{shortname}"
        )

    def aktivate(self):
        for komp in self.komponents:
            logger.debug(f"aktivating {komp.kind}.{komp.shortname}")
            komp.aktivate()

    def kreate_files(self):
        os.makedirs(self.konfig.target_dir, exist_ok=True)
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
                strukt = strukt or { "main": {}}
                for shortname in sorted(strukt.keys()):
                    logger.debug(f"kreating komponent {kind}.{shortname}")
                    self.kreate_komponent(kind, shortname)
            elif kind != "default":
                logger.warning(f"Unknown toplevel komponent {kind}")
