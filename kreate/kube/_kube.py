import logging
from typing import List
from ..kore import JinjaApp, Konfig
from ..krypt import KryptKonfig
from . import resource, templates

logger = logging.getLogger(__name__)


class KubeApp(JinjaApp):
    def __init__(self, konfig: Konfig):
        super().__init__(konfig)
        self.namespace = konfig.yaml["app"].get(
            "namespace", f"{self.appname}-{self.env}"
        )

    def register_std_templates(self) -> None:
        super().register_std_templates()
        self.register_resource_class(resource.Service)
        self.register_resource_class(resource.Deployment)
        self.register_resource_class(resource.PodDisruptionBudget)
        self.register_resource_class(resource.ConfigMap)
        self.register_resource_class(resource.Ingress)
        self.register_resource_class(resource.Egress)
        self.register_resource_class(resource.SecretBasicAuth)
        self.register_resource_class(resource.Secret)

        self.register_resource_file("HorizontalPodAutoscaler")
        self.register_resource_file("ServiceAccount")
        self.register_resource_file("ServiceMonitor")
        self.register_resource_file("CronJob")
        self.register_resource_file("StatefulSet", filename="Deployment.yaml")

    def register_resource_class(self, cls) -> None:
        package = templates
        super().register_template_class(cls, package=package)

    def register_resource_file(self, kind: str, filename: str = None) -> None:
        package = templates
        cls = resource.Resource
        super().register_template_file(kind, cls, filename=filename, package=package)


class KubeKonfig(KryptKonfig):
    pass
