import os
import logging
from ..kore import JinjaApp, Konfig
from ..krypt import KryptKonfig
from ..kore import _jinyaml
from . import resource, other_templates, resource_templates

logger = logging.getLogger(__name__)


class KubeApp(JinjaApp):
    def __init__(self, konfig: Konfig):
        super().__init__(konfig)
        self.namespace = self.appname + "-" + self.env

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


# Note the KubeKonfig class is totally unrelated to the
# kubeconfig file
def kreate_kubeconfig(konfig: Konfig):
    cluster_name = konfig.values.get("kubeconfig_cluster_name", None)
    if not cluster_name:
        cluster_name = f"{konfig.env}-cluster"
    user_name = konfig.values.get("kubeconfig_cluster_user_name", None)
    if not user_name:
        user_name = f"kreate-user-{konfig.env}"
    context_name = konfig.env
    # api_token should not be set in a file, just as environment variable
    token = os.getenv("KUBECONFIG_API_TOKEN")
    if not token:
        raise ValueError("environment var KUBECONFIG_API_TOKEN not set")
    api_token = token
    my = {
        "cluster_name": cluster_name,
        "cluster_user_name": user_name,
        "context_name": context_name,
        "api_token": api_token,
    }
    vars = {
            "konfig": konfig,
            "my": my,
            "val": konfig.values
        }
    loc = _jinyaml.FileLocation("kubeconfig.yaml", package=other_templates)
    data = _jinyaml.load_jinja_data(loc, vars)
    filename = f"{konfig.target_dir}/secrets/kubeconfig"
    logging.info(f"writing {filename}")
    os.makedirs(f"{konfig.target_dir}/secrets", exist_ok=True)
    with open(filename, "wt") as f:
        f.write(data)
