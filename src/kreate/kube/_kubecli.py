import os
import logging

from ..kore._korecli import kreate_files as kreate_files
from ..kore import Konfig
from ..krypt import _krypt, KryptCli, KryptKreator
from ._kust import KustApp
from ._kube import KubeConfig, KubeKonfig

logger = logging.getLogger(__name__)


class KubeKreator(KryptKreator):
    def kreate_konfig(self, filename: str = None) -> KubeKonfig:
        konfig = KubeKonfig(filename)
        self.tune_konfig(konfig)
        return konfig

    def tune_konfig(self, konfig: Konfig):
        super().tune_konfig(konfig)
        konfig._default_strukture_files.append("py:kreate.kube.templates:default-values.yaml")

    def kreate_app(self, konfig: Konfig) -> KustApp:
        app = KustApp(konfig)
        self.tune_app(app)
        return app


class KubeCli(KryptCli):
    def __init__(self, kreator: KubeKreator):
        super().__init__(kreator)
        self.add_subcommand(build, [], aliases=["b"])
        self.add_subcommand(diff, [], aliases=["d"])
        self.add_subcommand(apply, [], aliases=["a"])
        self.add_subcommand(test, [], aliases=["t"])
        self.add_subcommand(testupdate, [], aliases=["tu"])
        self.add_subcommand(kubeconfig, [])


def build(args):
    """output all the resources"""
    app = kreate_files(args)
    cmd = f"kustomize build {app.konfig.target_dir}"
    logger.info(f"running: {cmd}")
    os.system(cmd)


def diff(args):
    """diff with current existing resources"""
    app = kreate_files(args)
    cmd = (f"kustomize build {app.konfig.target_dir} "
           f"| kubectl --context={app.env} -n {app.namespace} diff -f - ")
    logger.info(f"running: {cmd}")
    os.system(cmd)


def apply(args):
    """apply the output to kubernetes"""
    app = kreate_files(args)
    cmd = f"kustomize build {app.konfig.target_dir} | kubectl apply --dry-run -f - "
    logger.info(f"running: {cmd}")
    os.system(cmd)


def test(args):
    """test output against test.out file"""
    _krypt._dekrypt_testdummy = True  # Do not dekrypt secrets for testing
    app = kreate_files(args)
    cmd = (f"kustomize build {app.konfig.target_dir} | diff "
           f"{app.konfig.dir}/expected-output-{app.appname}-{app.env}.out -")
    logger.info(f"running: {cmd}")
    os.system(cmd)


def testupdate(args):
    """update test.out file"""
    _krypt._dekrypt_testdummy = True  # Do not dekrypt secrets for testing
    app = kreate_files(args)
    cmd = (f"kustomize build {app.konfig.target_dir} "
           f"> {app.konfig.dir}/expected-output-{app.appname}-{app.env}.out")
    logger.info(f"running: {cmd}")
    os.system(cmd)

def kubeconfig(cli: KubeCli):
    # TODO: we only need a Dummy app
    konfig = cli.kreator.kreate_konfig(cli.args.konfig)
    kubeconfig = KubeConfig(konfig)
    #kubeconfig.aktivate() not needed?
    kubeconfig.kreate_file()
