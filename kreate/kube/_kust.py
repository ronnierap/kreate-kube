import logging

from ..kore import JinYamlKomponent, Module, App
from .resource import Resource
from .patch import Patch

logger = logging.getLogger(__name__)


class KustomizeModule(Module):
    def kreate_app_komponents(self, app: App):
        for res in app.komponents:
            if isinstance(res, Resource):
                self.kreate_patches(res)

    def kreate_patch(
        self,
        res: Resource,
        kind: str = None,
        shortname: str = None,
    ) -> None:
        cls = res.app.kind_classes[kind]
        if issubclass(cls, Patch):
            cls(res, shortname, kind)
        else:
            raise TypeError(f"class for {kind}.{shortname} is not a Patch but {cls}")

    def kreate_patches(self, res: Resource) -> None:
        if "patches" in res.strukture:
            for kind in sorted(res.strukture.get("patches").keys()):
                subpatches = res.strukture._get_path(f"patches.{kind}")
                if not subpatches.keys():
                    subpatches = {"main": {}}
                # use sorted because some patches, e.g. the MountVolumes
                # result in a list, were the order can be unpredictable
                for shortname in sorted(subpatches.keys()):
                    self.kreate_patch(res, kind=kind, shortname=shortname)


class Kustomization(JinYamlKomponent):
    def resources(self):
        return [res for res in self.app.komponents if isinstance(res, Resource)]

    def patches(self):
        return [res for res in self.app.komponents if isinstance(res, Patch)]

    def var(self, cm: str, varname: str):
        value = self.strukture._get_path(f"configmaps.{cm}.vars.{varname}")
        if not isinstance(value, str):
            value = self.app.konfig.get_path("var", {}).get(varname, None)
        if value is None:
            raise ValueError(f"var {varname} should not be None")
        return value

    def kopy_file(self, filename: str) -> str:
        location: str = self.app.konfig.yaml["file"][filename]
        if location.startswith("dekrypt:"):
            target = self.app.target_path / "secrets" / "files" / filename
            result = "secrets/files/" + filename
        else:
            target = self.app.target_path / "files" / filename
            result = "files/" + filename
        self.app.konfig.file_getter.kopy_file(location, target)
        return result

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
