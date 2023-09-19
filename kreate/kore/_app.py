import os
import logging
from typing import List, Set

from ._core import wrap, deep_update
from ._konfig import Konfig
from ._jinyaml import render_jinyaml

logger = logging.getLogger(__name__)


class App:
    def __init__(self, konfig: Konfig):
        self.appname = konfig.yaml["appname"]
        self.env = konfig.env
        self.konfig = konfig
        self.komponents = []
        self._kinds = {}
        self._strukt_dict = konfig.load_konfig_strukture_files()
        self.load_all_use_items()
        self.strukture = wrap(self._strukt_dict)

    def load_all_use_items(self):
        logger.debug("loading use files")
        already_loaded = set()
        to_load = self._strukt_dict.get("use", [])
        # keep loading until all is done
        while self.load_use_items(to_load, already_loaded) > 0:
            # possible new use items are added
            to_load = self._strukt_dict.get("use", [])

    def load_use_items(self, to_load: List[str], already_loaded: Set[str]) -> int:
        count = 0
        for fname in to_load:
            if fname in already_loaded:
                continue
            count += 1
            already_loaded.add(fname)
            logger.info(f"using {fname}")
            data = self.konfig.load_data(fname)
            val_yaml = render_jinyaml(data, self.konfig.yaml)
            if val_yaml:  # it can be empty
                deep_update(self._strukt_dict, val_yaml)
        logger.debug(f"loaded {count} new use files")
        return count

    def komponent_naming(self, kind: str, shortname: str) -> str:
        naming = self.konfig.yaml.get("system", {}).get("naming", {})
        formatstr: str = naming.get(kind, None)
        if formatstr:
            return formatstr.format(
                kind=kind, shortname=shortname, appname=self.appname
            )
        return None

    def add(self, res) -> None:
        if not res.skip:
            self.komponents.append(res)
        map = self._kinds.get(res.kind.lower(), None)
        if map is None:
            map = wrap({})
            self._kinds[res.kind.lower()] = map
        map[res.shortname] = res

    def __getattr__(self, attr):
        if attr in self.__dict__ or attr == "_dict":
            return super().__getattribute__(attr)
        return self._kinds.get(attr, None)

    def kreate_komponent(self, kind: str, shortname: str = None):
        raise NotImplementedError(f"can not create komponent for {kind}.{shortname}")

    def aktivate(self):
        for komp in self.komponents:
            logger.debug(f"aktivating {komp.kind}.{komp.shortname}")
            komp.aktivate()

    def kreate_files(self):
        os.makedirs(self.konfig.target_dir, exist_ok=True)
        for komp in self.komponents:
            if komp.filename:
                if komp.dirname:
                    logger.info(f"kreating file {komp.dirname}/{komp.filename}")
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
