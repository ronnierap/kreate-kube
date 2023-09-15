import os
import shutil
import logging
from ..kore import JinjaApp, Konfig
from ..krypt import KryptKonfig, krypt_functions
from ..kore import _jinyaml
from . import resource, resource_templates

logger = logging.getLogger(__name__)


class KubeApp(JinjaApp):
    def __init__(self, konfig: Konfig):
        super().__init__(konfig)
        self.namespace = konfig.yaml["val"].get(
            "namespace", f"{self.appname}-{self.env}"
        )

    def register_std_templates(self) -> None:
        super().register_std_templates()
        self.register_resource_class(resource.Service, "svc")
        self.register_resource_class(resource.Deployment, "depl")
        self.register_resource_class(resource.PodDisruptionBudget, "pdb")
        self.register_resource_class(resource.ConfigMap, "cm")
        self.register_resource_class(resource.Ingress)
        self.register_resource_class(resource.Egress)
        self.register_resource_class(resource.SecretBasicAuth)
        self.register_resource_class(resource.Secret)

        self.register_resource_file("HorizontalPodAutoscaler", aliases="hpa")
        self.register_resource_file("ServiceAccount")
        self.register_resource_file("ServiceMonitor")
        self.register_resource_file("CronJob")
        self.register_resource_file("StatefulSet", filename="Deployment.yaml")

    def register_resource_class(
        self: str, cls, aliases=None, package=None
    ) -> None:
        package = package or resource_templates
        super().register_template_class(
            cls,
            filename=None,
            aliases=aliases,
            package=package,
        )

    def register_resource_file(
        self,
        cls: str,
        filename: str = None,
        aliases=None,
        package=None,
    ) -> None:
        package = package or resource_templates
        super().register_template_file(
            cls, filename=filename, aliases=aliases, package=package
        )

    def _default_template_class(self):
        return resource.Resource



class KubeKonfig(KryptKonfig):
    pass
