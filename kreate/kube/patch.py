import logging

from ..kore import deep_update
from ..kore import JinYamlKomponent
from ..kore._komp import KomponentKlass
from .resource import Resource, Egress

logger = logging.getLogger(__name__)


__all__ = [
    "Patch",
    "AddEgressLabelsPatch",
]


class Patch(JinYamlKomponent):
    # TODO the signature differs from other komponents, and might not work
    # in KomponentKlass.kreate_komponent. Needs some redesign
    def __init__(self, target: Resource, klass: KomponentKlass, shortname: str):
        self.target = target
        super().__init__(target.app, klass=klass, shortname=shortname)

    def __str__(self):
        return (f"<Patch {self.target.id}: {self.id}>")

    def get_filename(self):
        return (
            f"patches/{self.target.id}-{self.id}.yaml"
        )

    def _template_vars(self):
        return {**super()._template_vars(), "target": self.target}

    def _find_strukture(self):
        target_struk = self.target.strukture.get(f"patches.{self.id}", {})
        return target_struk

    def _field(self, fieldname: str, default=None):
        if fieldname in self.strukture:
            return self.strukture[fieldname]
        if fieldname in self.target.strukture:
            return self.target.strukture[fieldname]
        return super()._field(fieldname, default=default)

class CustomPatch(Patch):
    def get_template_location(self) -> str:
        return self.strukture.get("template")


class EgressLabels(Patch):
    def egresses(self):
        return [k for k in self.app.komponents if isinstance(k, Egress)]


class MultiPatch(Patch):
    def __init__(self, target: Resource, klass: KomponentKlass, shortname: str):
        super().__init__(target, klass, shortname)
        patches = klass.info.get("patches")
        patches = patches or klass.info.get("template") # TODO remove in kreate 2.0
        for patch_name in patches:
            klass = self.app.klasses[patch_name]
            klass.kreate_komponent(target, "main")

    def skip(self):
        return True
