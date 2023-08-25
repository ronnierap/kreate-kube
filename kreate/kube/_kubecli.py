import os
import logging

from ..kore import App
from ..kore import Konfig
from .. import krypt
from ..krypt import krypt_functions
from ._kust import KustApp
from ._kube import KubeKonfig, kreate_kubeconfig

logger = logging.getLogger(__name__)


class KubeKreator(krypt.KryptKreator):
    def kreate_konfig(self, filename: str = None) -> KubeKonfig:
        if not self.konfig:
            self.konfig = KubeKonfig(filename)
            self.tune_konfig(self.konfig)
        return self.konfig

    def tune_konfig(self, konfig: Konfig):
        super().tune_konfig(konfig)
        konfig._default_strukture_files.append(
            "py:kreate.kube.other_templates:kube-defaults.yaml"
        )

    def kreate_app(self, konfig: Konfig, tune_app=True) -> KustApp:
        app = KustApp(konfig)
        if tune_app:  # Ugly hack for view_templates
            self.tune_app(app)
        return app


class KubeCli(krypt.KryptCli):
    def __init__(self, kreator: KubeKreator):
        super().__init__(kreator)
        self.add_subcommand(files, [], aliases=["f"])
        self.add_subcommand(build, [], aliases=["b"])
        self.add_subcommand(diff, [], aliases=["d"])
        self.add_subcommand(apply, [], aliases=["a"])
        cmd = self.add_subcommand(test, [], aliases=["t"])
        cmd.add_argument(
            "-e",
            "--expected-output",
            help="file with expected output of build",
            action="store",
            default=None,
        )

        cmd = self.add_subcommand(testupdate, [], aliases=["tu"])
        cmd.add_argument(
            "-e",
            "--expected-output",
            help="file with expected output of build",
            action="store",
            default=None,
        )

        self.add_subcommand(kubeconfig, [])

    def default_command(self):
        files(self)


def kreate_files(cli: KubeCli) -> KustApp:
    konfig: Konfig = cli.kreator.kreate_konfig(cli.args.konfig)
    app: App = cli.kreator.kreate_app(konfig)
    app.kreate_files()
    return app


def files(cli: KubeCli) -> None:
    """kreate all the files (default command)"""
    kreate_files(cli)


def build(cli: KubeCli) -> None:
    """output all the resources"""
    app = kreate_files(cli)
    cmd = f"kustomize build {app.konfig.target_dir}"
    logger.info(f"running: {cmd}")
    os.system(cmd)


def diff(cli: KubeCli) -> None:
    """diff with current existing resources"""
    app = kreate_files(cli)
    cmd = (
        f"kustomize build {app.konfig.target_dir} "
        f"| kubectl --context={app.env} -n {app.namespace} diff -f - "
    )
    logger.info(f"running: {cmd}")
    os.system(cmd)


def apply(cli: KubeCli) -> None:
    """apply the output to kubernetes"""
    app = kreate_files(cli)
    cmd = (
        f"kustomize build {app.konfig.target_dir} "
        f"| kubectl apply --dry-run -f - "
    )
    logger.info(f"running: {cmd}")
    os.system(cmd)


def test(cli: KubeCli) -> None:
    """test output against expected-output-<app>-<env>.out file"""
    # Do not dekrypt secrets for testing
    krypt_functions._dekrypt_testdummy = True
    app = kreate_files(cli)
    expected = (
        cli.args.expected_output
        or f"{app.konfig.dir}/expected-output-{app.appname}-{app.env}.out"
    )
    cmd = f"kustomize build {app.konfig.target_dir} | diff {expected} -"
    logger.info(f"running: {cmd}")
    os.system(cmd)


def testupdate(cli: KubeCli) -> None:
    """update expected-output-<app>-<env>.out file"""
    # Do not dekrypt secrets for testing
    krypt_functions._dekrypt_testdummy = True
    app = kreate_files(cli)
    expected = (
        cli.args.expected_output
        or f"{app.konfig.dir}/expected-output-{app.appname}-{app.env}.out"
    )
    cmd = f"kustomize build {app.konfig.target_dir} >{expected}"
    logger.info(f"running: {cmd}")
    os.system(cmd)


def kubeconfig(cli: KubeCli):
    """kreate a kubeconfig file from a template"""
    konfig = cli.kreator.kreate_konfig(cli.args.konfig)
    kreate_kubeconfig(konfig)
