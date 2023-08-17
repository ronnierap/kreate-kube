import logging

from ..kore import FileLocation, AppDef
from ..kore import DeepChain
from ..kore import JinYamlKomponent
from ._kube import KubeApp, Resource, Egress
from . import templates
from .templates import patches

logger = logging.getLogger(__name__)


class KustApp(KubeApp):
    def __init__(self, appdef: AppDef):
        super().__init__(appdef)
        self.register_templates_from_appdef("patch_templates", Patch)

    def register_std_templates(self) -> None:
        super().register_std_templates()
        self.register_template_class(Kustomization, package=templates)
        self.register_template_class(AddEgressLabelsPatch, package=patches)
        self.register_template_file("AntiAffinityPatch", cls=Patch, package=patches)
        self.register_template_file("HttpProbesPatch", cls=Patch, package=patches)
        self.register_template_file("MountVolumeFiles", cls=Patch, package=patches)

    def kreate_komponents_from_strukture(self):
        super().kreate_komponents_from_strukture()
        for res in self.komponents:
            if isinstance(res, Resource):
                self.kreate_patches(res)

    def kreate_patch(
            self,
            res: Resource,
            kind: str = None,
            shortname: str = None,
            **kwargs):
        cls = self.kind_classes[kind]
        templ = self.kind_templates[kind]
        if issubclass(cls, Patch):
            return cls(res, shortname, kind, template=templ, **kwargs)
        raise TypeError(
            f"class for {kind}.{shortname} is not a Patch but {cls}")

    def kreate_patches(self, res: Resource) -> None:
        if "patches" in res.strukture:
            for kind in sorted(res.strukture.patches.keys()):
                subpatches = res.strukture.patches[kind]
                if not subpatches.keys():
                    subpatches={ "main": {} }
                # use sorted because some patches, e.g. the MountVolumes
                # result in a list, were the order can be unpredictable
                for shortname in sorted(subpatches.keys()):
                    self.kreate_patch(res, kind=kind, shortname=shortname)


class Kustomization(JinYamlKomponent):
    def resources(self):
        return [
            res for res in self.app.komponents if isinstance(
                res, Resource)]

    def patches(self):
        return [res for res in self.app.komponents if isinstance(res, Patch)]

    @property
    def filename(self):
        return "kustomization.yaml"


class Patch(JinYamlKomponent):
    def __init__(
            self,
            target: Resource,
            shortname: str = None,
            kind: str = None,
            template: FileLocation = None,
            **kwargs):
        self.target = target
        super().__init__(
            target.app,
            shortname=shortname,
            kind=kind,
            template=template,
            **kwargs)

    def __str__(self):
        return (f"<Patch {self.target.kind}.{self.target.shortname}"
                f":{self.kind}.{self.shortname}>")

    @property
    def dirname(self):
        return self.app.appdef.target_dir + "/patches"

    @property
    def filename(self):
        return f"{self.target.kind}-{self.target.shortname}-{self.kind}-{self.shortname}.yaml"

    def _template_vars(self):
        return {**super()._template_vars(), "target": self.target}

    def _find_strukture(self):
        root_strukture = super()._find_strukture()
        typename = self.kind
        tar_struk = self.target.strukture.get("patches", {})
        if typename in tar_struk and self.shortname in tar_struk[typename]:
            logger.debug(
                f"using embedded strukture {typename}.{self.shortname}"
                f" from {self.target.kind}.{self.target.shortname}")
            # The embedded_strukture is first,
            # since the root_strukture will contain all default values
            embedded_strukture = tar_struk[typename][self.shortname]
            return DeepChain(embedded_strukture, root_strukture)
        return root_strukture


class AddEgressLabelsPatch(Patch):
    def egresses(self):
        return [k for k in self.app.komponents if isinstance(k, Egress)]
