import logging
from pathlib import Path

from ..kore import JinYamlKomponent, Module, App, KomponentKlass
from .resource import Resource, MultiDocumentResource
from .patch import Patch, CustomPatch

logger = logging.getLogger(__name__)


class KustomizeModule(Module):
    def init_app(self, app: App) -> None:
        app.register_klass(CustomPatch)

    def kreate_app_komponents(self, app: App):
        for res in app.komponents:
            if isinstance(res, Resource):
                self.kreate_embedded_patches(app, res)

    def kreate_embedded_patches(self, app: App, res: Resource) -> None:
        if "patches" in res.strukture:
            for patch_name in sorted(res.strukture.get("patches").keys()):
                subpatches = res.strukture.get_path(f"patches.{patch_name}")
                klass = res.app.klasses[patch_name]
                if not subpatches.keys():
                    subpatches = {"main": {}}
                # use sorted because some patches, e.g. the MountVolumes
                # result in a list, were the order can be unpredictable
                for shortname in sorted(subpatches.keys()):
                    Patch.from_target(app, klass, shortname, target_id=res.id)


class Kustomization(JinYamlKomponent):
    def resources(self):
        return [
            res
            for res in self.app.komponents
            if isinstance(res, Resource) or isinstance(res, MultiDocumentResource)
        ]

    def patches(self):
        return [res for res in self.app.komponents if isinstance(res, Patch)]

    def var(self, cm: str, varname: str):
        value = self.strukture.get_path(f"configmaps.{cm}.vars.{varname}")
        if not isinstance(value, str):
            value = self.app.konfig.get_path("var", {}).get(varname, None)
        if value is None:
            raise ValueError(f"var {varname} should not be None")
        return value


    def _write_data(self, data: str, target: Path) -> None:
        dir = target.parent
        dir.mkdir(parents=True, exist_ok=True)
        if isinstance(data, bytes):
            data = data.decode()
        target.write_text(data)

    def _find_and_kopy_file(self, filename: str, target: Path, search_path) -> str:
        if loc := self.app.konfig.get_path("file", {}).get(filename):
                logger.info(f"kopying file {loc} to {target}")
                data = self.app.konfig.file_getter.get_data(loc)
                self._write_data(data, target)
                return
        logger.verbose(f"looking for {filename} in {search_path}")
        for path in search_path:
            logger.verbose(f"looking for {filename} to kopy in {path}")
            p =  str(Path(path) / filename)
            data = self.app.konfig.file_getter.get_data(p)
            if data:
                logger.info(f"kopying file {path} to {target}")
                self._write_data(data, target)
                return
        raise ValueError(f"Could not find file {filename} in {search_path}, add it to file: section")

    def kopy_file(self, filename: str, dest: str = "files") -> str:
        search_path = self.app.konfig.get_path("system.search_path.kopy_file", [])
        target = self.app.target_path / Path(dest) / filename
        result = Path(dest) / filename
        self._find_and_kopy_file(filename, target, search_path)
        return str(result)

    def kopy_secret_file(self, filename: str, dest: str = "secrets/files") -> str:
        search_path = self.app.konfig.get_path("system.search_path.kopy_secret_file", [])
        target = self.app.target_path / Path(dest) / filename
        result = Path(dest) / filename
        self._find_and_kopy_file(filename, target, search_path)
        self.app.kontext.add_cleanup_path(target)
        return str(result)

    def get_filename(self):
        return "kustomization.yaml"

    def aktivate(self):
        super().aktivate()
        self.remove_vars()

    def remove_vars(self):
        removals = self.strukture.get("remove_vars", {})
        for cm_to_remove in removals:
            for cm in self.get_path("configMapGenerator", {}):
                if cm["name"] == cm_to_remove:
                    for var in self.strukture["remove_vars"][cm_to_remove]:
                        found = False
                        for idx, v in enumerate(cm["literals"]):
                            if v.startswith(var + "="):
                                found = True
                                logger.info(f"removing var {cm_to_remove}.{v}")
                                cm["literals"].pop(idx)
                        if not found:
                            logger.warning(
                                f"could not find var to remove {cm_to_remove}.{var}"
                            )
