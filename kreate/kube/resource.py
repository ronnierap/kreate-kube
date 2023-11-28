import logging

from ..kore import JinYamlKomponent, wrap
from ..krypt.krypt_functions import dekrypt_str

logger = logging.getLogger(__name__)


__all__ = [
    "Resource",
    "Workload",
    "ConfigMap",
    "Egress",
]


class Resource(JinYamlKomponent):
    def aktivate(self):
        super().aktivate()
        self.add_metadata()

    def __str__(self):
        return f"<Resource {self.kind}.{self.shortname} {self.name}>"

    def get_filename(self):
        return f"resources/{self.kind}-{self.name}.yaml"

    def add_metadata(self):
        for key in self.strukture.get("annotations", {}):
            self.yaml.get("metadata.annotations")[key] = self.strukture.get("annotations")[key]
        for key in self.strukture.get("labels", {}):
            self.yaml._set_path(f"metadata.labels.{key}",  self.strukture._get_path(f"labels.{key}"))

    #def annotation(self, name: str, val: str) -> None:
    #    self.yaml._set_path(f"metadata.annotations.{name}", val)
    #
    #def label(self, name: str, val: str) -> None:
    #    self.yaml._set_path(f"metadata.labels.{name}", val)

    def load_file(self, filename: str) -> str:
        with open(f"{self.app.konfig.dir}/{filename}") as f:
            return f.read()


class Workload(Resource):
    def aktivate(self):
        super().aktivate()
        self.add_container_items()
        self.remove_container_items()

    def add_container_items(self):
        additions = self.strukture.get("add_to_container", {})
        if additions:
            container = wrap(self.get_path("spec.template.spec.containers")[0])
            for path in additions:
                container._set_path(path, additions[path])

    def remove_container_items(self):
        additions = self.strukture.get("remove_from_container", {})
        if additions:
            container = wrap(self.get_path("spec.template.spec.containers")[0])
            for path in additions:
                container._del_path(path)

    def pod_annotation(self, name: str, val: str) -> None:
        self.set_path(f"spec.template.metadata.annotations.{name}", val)

    def pod_label(self, name: str, val: str) -> None:
        self.set_path(f"spec.template.metadata.labels.{name}", val)


class Egress(Resource):
    """This is a Marker class used in EgressLabels patch"""


class ConfigMap(Resource):
    def var(self, varname: str):
        value = self.strukture.vars[varname]
        if not isinstance(value, str):
            value = self.app.konfig.get_path(f"var.{varname}", None)
        if value is None:
            raise ValueError(f"var {varname} should not be None")
        return value

    def file_data(self, filename: str) -> str:
        location: str = self.app.konfig.yaml["file"][filename]
        return self.app.konfig.load_repo_file(location)


class Secret(Resource):
    def file_data(self, filename: str) -> str:
        location: str = self.app.konfig.yaml["file"][filename]
        return self.app.konfig.load_repo_file(location)

    def get_filename(self):
        return f"secrets/resources/{self.kind}-{self.name}.yaml"

    def is_secret(self) -> bool:
        return True

    def secret(self, varname: str):
        value = self.strukture._get_path(f"vars.{varname}")
        if not isinstance(value, str):
            value = self.app.konfig.get_path(f"secret.var.{varname}", None)
        if value is None:
            raise ValueError(f"missing secret.var.{varname}")
        if value.startswith("escape:"):
            # escape mechanism is a value needs to start with dekrypt:
            value = value[7:]
        elif value.startswith("dekrypt:"):
            value = dekrypt_str(value[8:])
        if value is None:
            raise ValueError(f"secret {varname} should not be None")
        return value


class SecretBasicAuth(Resource):
    def users(self):
        result = []
        for usr in self.strukture.get("users", []):
            secret = self.app.konfig.get_path(f"secret.basic_auth.{usr}")
            if not secret:
                raise LookupError(f"could not find secret.basic_auth.{usr}")
            entry = dekrypt_str(secret)
            result.append(f"{usr}:{entry}")
        result.append("")  # for the final newline
        return "\n".join(result)

    def get_filename(self):
        return f"secrets/resources/{self.kind}-{self.name}.yaml"

    def is_secret(self) -> bool:
        return True
