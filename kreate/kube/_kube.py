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
        self.namespace = konfig.values.get(
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

    def aktivate(self):
        self.kopy_files()
        super().aktivate()

    def kopy_files(self):
        target_dir = self.konfig.target_dir
        if os.path.exists(target_dir) and os.path.isdir(target_dir):
            logger.info(f"removing target directory {target_dir}")
            shutil.rmtree(target_dir)
        self.konfig.kopy_files("files", "files")
        self.konfig.kopy_files(
            "secret_files", "secrets/files", dekrypt_default=True
        )


class KubeKonfig(KryptKonfig):
    def load(self):
        if "values" not in self.yaml:
            logger.debug("adding default values file(s)")
            self.yaml["values"] = self.default_values_files()
        if "secrets" not in self.yaml:
            logger.debug("adding default secrets file(s)")
            self.yaml["secrets"] = self.default_secrets_files()
        if "strukture" not in self.yaml:
            logger.debug("adding default strukture file(s)")
            self.yaml["strukture"] = self.default_strukture_files()
        if "krypt_key" not in self.yaml:
            psw = self.default_krypt_key()
            if not psw:
                logger.warning(f"no dekrypt key provided")
            self.yaml["krypt_key"] = psw
        super().load()

    def default_values_files(self):
        return [f"values-{self.appname}-{self.env}.yaml"]

    def default_secrets_files(self):
        # if an application does not have any secrets, the files can be specified as
        # secrets: []
        # alternatively we could build a check to only include
        # the file below if it exists
        return [f"secrets-{self.appname}-{self.env}.yaml"]

    def default_strukture_files(self):
        return [f"{self.appname}-strukture.yaml"]

    def default_krypt_key(self):
        env_varname = self.default_krypt_key_env_var()
        logger.debug(f"getting dekrypt key from {env_varname}")
        psw = os.getenv(env_varname)
        if not psw:
            logger.warning(
                f"no dekrypt key given in environment var {env_varname}"
            )
        return psw

    def default_krypt_key_env_var(self):
        return "KREATE_KRYPT_KEY_" + self.env.upper()

    def kopy_files(self, key, target_subdir, dekrypt_default=False):
        file_list = self.yaml.get("kopy_" + key, [])
        if not file_list:
            return
        os.makedirs(f"{self.target_dir}/{target_subdir}", exist_ok=True)
        for file in file_list:
            dekrypt = file.get("dekrypt", dekrypt_default)
            name = file.get("name", None)
            if not name:
                raise ValueError(
                    f"file in konfig {key}should have name {file}"
                )
            from_ = file.get(
                "from", f"{key}/{name}" + (".encrypted" if dekrypt else "")
            )
            template = file.get("template", False)
            loc = _jinyaml.FileLocation(from_, dir=self.dir)
            if template:
                vars = {
                    "konfig": self,
                    "val": self.values,
                    "secret": self.secrets,
                }
                logger.debug(f"rendering template {from_}")
                prefix = "rendered template " + from_
                data = _jinyaml.load_jinja_data(loc, vars)
            else:
                prefix = from_
                data = _jinyaml.load_data(loc)
            if dekrypt:
                prefix = "dekrypted " + prefix
                data = krypt_functions.dekrypt_str(data)
            with open(f"{self.target_dir}/{target_subdir}/{name}", "w") as f:
                logger.info(
                    f"kreating file {key}/{name} from {prefix}"
                )  # TODO: log earlier
                f.write(data)
