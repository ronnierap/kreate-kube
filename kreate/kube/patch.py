import logging

from ..kore import FileLocation
from ..kore import DeepChain
from ..kore import JinYamlKomponent
from .resource import Resource, Egress

logger = logging.getLogger(__name__)


__all__ = [
    "Patch",
    "AddEgressLabelsPatch",
]


class Patch(JinYamlKomponent):
    def __init__(
        self,
        target: Resource,
        shortname: str = None,
        kind: str = None,
        template: FileLocation = None,
    ):
        self.target = target
        super().__init__(
            target.app,
            shortname=shortname,
            kind=kind,
            template=template,
        )

    def __str__(self):
        return (
            f"<Patch {self.target.kind}.{self.target.shortname}"
            f":{self.kind}.{self.shortname}>"
        )

    @property
    def dirname(self):
        return "patches"

    @property
    def filename(self):
        return (
            f"{self.target.kind}-{self.target.shortname}"
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
            return DeepChain(embedded_strukture, root_strukture)
        return root_strukture


class EgressLabels(Patch):
    def egresses(self):
        return [k for k in self.app.komponents if isinstance(k, Egress)]
