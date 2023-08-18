import os
import logging
from ..kore import JinjaApp, Konfig, JinYamlKomponent
from ..krypt import KryptKonfig
from ..kore._jinyaml import FileLocation
from . import resource, other_templates, resource_templates

logger = logging.getLogger(__name__)


class KubeApp(JinjaApp):
    def __init__(self, konfig: Konfig):
        super().__init__(konfig)
        self.namespace = self.appname + "-" + self.env
        #self.target_dir = "./build/" + self.namespace

    def register_std_templates(self) -> None:
        super().register_std_templates()
        self.register_resource_class(resource.Service, "svc")
        self.register_resource_class(resource.Deployment, "depl")
        self.register_resource_class(resource.PodDisruptionBudget, "pdb")
        self.register_resource_class(resource.ConfigMap, "cm")
        self.register_resource_class(resource.Ingress)
        self.register_resource_class(resource.Egress)
        self.register_resource_class(resource.SecretBasicAuth)

        self.register_resource_file("HorizontalPodAutoscaler", aliases="hpa")
        self.register_resource_file("ServiceAccount")
        self.register_resource_file("ServiceMonitor")
        self.register_resource_file("Secret")
        self.register_resource_file("CronJob")
        self.register_resource_file("StatefulSet", filename="Deployment.yaml")

    def register_resource_class(self: str, cls: str, aliases=None) -> None:
        super().register_template_class(
            cls,
            filename=None,
            aliases=aliases,
            package=resource_templates)

    def register_resource_file(self,
            cls: str,
            filename: str = None,
            aliases=None) -> None:
        super().register_template_file(
            cls,
            filename=filename,
            aliases=aliases,
            package=resource_templates)


    def _default_template_class(self):
        return resource.Resource


class KubeKonfig(KryptKonfig):
    pass
    #def __init__(self, filename: str = None):
    #    super().__init__(filename=filename)


# TODO: KubeConfig does not have an app to be added to
# This needs all kinds of workarounds that might need some refactoring
class KubeConfig(JinYamlKomponent):
    def __init__(self, konfig: Konfig):
        self.konfig = konfig
        template_loc = FileLocation("kubeconfig.yaml", package=other_templates)
        super().__init__(None, "main", template=template_loc)
        self.cluster_name = konfig.values.get(
            "kubeconfig_cluster_name",
            f"{konfig.env}-cluster")
        self.cluster_user_name = konfig.values.get(
            "kubeconfig_cluster_user_name",
            f"kreate-user-{konfig.env}")
        self.context_name = konfig.env
        # api_token should not be set in a file, just as environment variable
        token = os.getenv("KUBECONFIG_API_TOKEN")
        if not token:
            raise ValueError("environment var KUBECONFIG_API_TOKEN not set")
        self.api_token = token
        self.aktivate()

    def _template_vars(self):
        return {
            "konfig": self.konfig,
            "my": self,
            "val": self.konfig.values
        }

    def calc_name(self):
        return "kubeconfig"

    @property
    def filename(self):
        return "kubeconfig"

    @property
    def dirname(self):
        return "build"
