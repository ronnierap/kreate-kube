import os
import logging
from ..kore import Konfig
from ..kore import _jinyaml
from . import other_templates

logger = logging.getLogger(__name__)


# Note the KubeKonfig class is totally unrelated to the
# kubeconfig file
def kreate_kubeconfig(konfig: Konfig, force=False):
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
    vars = {"konfig": konfig, "my": my, "val": konfig.values}
    loc = _jinyaml.FileLocation("kubeconfig.yaml", package=other_templates)
    data = _jinyaml.load_jinja_data(loc, vars)
    filename = os.getenv("KUBECONFIG")
    if not filename:
        filename = f"{konfig.target_dir}/secrets/kubeconfig"
        os.makedirs(f"{konfig.target_dir}/secrets", exist_ok=True)
    if os.path.exists(filename):
        if force:
            logging.info(f"overwriting {filename}")
        else:
            raise FileExistsError(
                f"kubeconfig file {filename} already exists "
                "use --force option to overwrite"
            )
    else:
        logging.info(f"writing new {filename}")
    with open(filename, "wt") as f:
        f.write(data)
