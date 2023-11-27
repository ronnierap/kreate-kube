import logging

from ..kore import deep_update
from ..kore import JinYamlKomponent
from .resource import Resource, Egress
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ._kust import KustomizeModule

logger = logging.getLogger(__name__)


__all__ = [
    "Patch",
    "AddEgressLabelsPatch",
]


class Patch(JinYamlKomponent):
    def __init__(self, target: Resource, shortname: str, kind: str):
        self.target = target
        super().__init__(target.app, shortname=shortname, kind=kind)

    def __str__(self):
        return (
            f"<Patch {self.target.kind}.{self.target.shortname}"
            f":{self.kind}.{self.shortname}>"
        )

    def get_filename(self):
        return (
            f"patches/{self.target.kind}-{self.target.shortname}"
            f"-{self.kind}-{self.shortname}.yaml"
        )

    def _template_vars(self):
        return {**super()._template_vars(), "target": self.target}

    def _find_strukture(self):
        root_strukture = super()._find_strukture()
        typename = self.kind
        tar_struk = self.target.strukture.get("patches", {})
        if typename in tar_struk and self.shortname in tar_struk[typename]:
            logger.debug(
                f"using embedded strukture {typename}.{self.shortname}"
                f" from {self.target.kind}.{self.target.shortname}"
            )
            # The embedded_strukture is first,
            # since the root_strukture will contain all default values
            embedded_strukture = tar_struk[typename][self.shortname]
            deep_update(root_strukture, embedded_strukture)
        return root_strukture

    def _field(self, fieldname: str, default=None):
        if fieldname in self.strukture:
            return self.strukture[fieldname]
        if fieldname in self.target.strukture:
            return self.target.strukture[fieldname]
        return super()._field(fieldname, default=default)


class EgressLabels(Patch):
    def egresses(self):
        return [k for k in self.app.komponents if isinstance(k, Egress)]


class MultiPatch(Patch):
    def __init__(self, target: Resource, shortname: str, kind: str):
        super().__init__(target, shortname, kind)
        patches = target.app.konfig.yaml["system"]["template"][kind]["template"]
        for patch_name in patches:
            cls = target.app.kind_classes[patch_name]
            cls(target, "main", patch_name)

    def skip(self):
        return True
