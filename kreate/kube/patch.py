import logging

from ..kore import deep_update
from ..kore import JinYamlKomponent, App
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
    def __init__(self, app: App, klass: KomponentKlass, shortname: str, target_id : str = None):
        super().__init__(app=app, klass=klass, shortname=shortname)
        # The target_id is to find the target, it can be passed in explicitely,
        # but also provide in the strukture. If both are empty, the shortname is used.
        target_id = target_id or self.strukture.get("target")
        self.target_id = target_id or shortname
        # The target will be resolved at aktivation, when all komponents are known
        self.target = None

    def aktivate(self):
        self.target = self.app.komponents_by_id[self.target_id]
        super().aktivate()

    def __str__(self):
        return f"<Patch {self.target_id}: {self.id}>"

    def get_filename(self):
        return f"patches/{self.target_id}-{self.id}.yaml"

    def _template_vars(self):
        return {**super()._template_vars(), "target": self.target}

    def _find_strukture(self):
        if result := super()._find_strukture():
            return result
        return self.app.konfig.get_path(f"{self.target_id}.patches.{self.id}", {})

    def _field(self, fieldname: str, default=None):
        if fieldname in self.strukture:
            return self.strukture[fieldname]
        if result := self.target.strukture.get_path(f"field.{fieldname}"):
            return result
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
        patches = patches or klass.info.get("template")  # TODO remove in kreate 2.0
        for patch_name in patches:
            klass = self.app.klasses[patch_name]
            klass.kreate_komponent(target, "main")

    def skip(self):
        return True
