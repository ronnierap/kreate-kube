import logging
import difflib
import subprocess

from .. import krypt
from ..krypt import krypt_functions
from ._kust import KustApp
from ._kube import KubeKonfig

logger = logging.getLogger(__name__)


class KubeCli(krypt.KryptCli):
    def __init__(self, *, app_class=KustApp):
        super().__init__()
        self._app_class = app_class
        self.add_subcommand(build, [], aliases=["b"])
        self.add_subcommand(diff, [], aliases=["d"])
        self.add_subcommand(apply, [], aliases=["a"])
        self.add_subcommand(test, [], aliases=["t"])
        self.add_subcommand(test_update, [], aliases=["tu"])
        self.add_subcommand(test_diff, [], aliases=["td"])
        self.add_subcommand(test_diff_update, [], aliases=["tdu"])

    def get_packages(self):
        return ["kreate-kube"]

    def kreate_konfig(self, filename: str) -> KubeKonfig:
        return KubeKonfig(filename, dict_=self.calc_dict(), inkludes=self.args.inklude)

    def kreate_app(self) -> KustApp:
        return self._app_class(self.konfig())



def build(cli: KubeCli) -> None:
    """output all the resources"""
    cli.run_command("build")


def diff(cli: KubeCli) -> None:
    """diff with current existing resources"""
    cli.run_command("diff")


def apply(cli: KubeCli) -> None:
    """apply the output to kubernetes"""
    cli.run_command("apply")

def expected_file(cli: KubeCli) -> str:
    app = cli.app()
    return (
        cli.konfig().get_path("tests.expected_output")
        or f"{app.konfig.dir}/expected-output-{app.appname}-{app.env}.out"
    )

def build_output(cli: KubeCli) -> str:
    # Do not dekrypt secrets for testing
    krypt_functions._dekrypt_testdummy = True
    cli.kreate_files()
    return subprocess.check_output(["kustomize","build", str(cli.app().target_path)]).decode()


def test_result(cli: KubeCli, n=0):
    ignores = cli.konfig().get_path("tests.ignore")
    build_lines = build_output(cli).splitlines()
    expected_lines = cli.konfig().load_repo_file(expected_file(cli)).splitlines()
    diff = difflib.context_diff(expected_lines, build_lines, n=n)
    stars_loc = ""
    stars_loc_old = "old"
    diff_result = []
    for line in diff:
        if line.startswith("*** "):
            stars_loc = line.strip()
            continue
        elif line.startswith("***"):
            continue
        elif line.startswith("---"):
            continue
        ignore = False
        for ign in ignores:
            if ign in line:
                ignore = True
        if not ignore:
            if stars_loc_old is not stars_loc:
                stars_loc_old = stars_loc
                diff_result.append(stars_loc)
            diff_result.append(line)
    return diff_result


def test(cli: KubeCli) -> None:
    """test output against expected-output-<app>-<env>.out file"""
    diff_result = test_result(cli)
    print("\n".join(diff_result))


def test_update(cli: KubeCli) -> None:
    """test output against expected-output-<app>-<env>.out file"""
    cli.konfig().save_repo_file(expected_file(cli), build_output(cli))


def test_diff(cli: KubeCli):
    """test output against expected-output-<app>-<env>.out file"""
    diff_result = test_result(cli)
    expected_diff = cli.konfig().get_path("tests.expected_diff")
    expected_diff_lines = cli.konfig().load_repo_file(expected_diff).splitlines()
    diff2 = difflib.context_diff(expected_diff_lines, diff_result, n=0)
    for line in diff2:
        print(line.strip())

def test_diff_update(cli: KubeCli) -> None:
    """update expected-output-<app>-<env>.out file"""
    diff_result = test_result(cli)
    expected_diff_file =cli.konfig().get_path("tests.expected_diff")
    cli.konfig().save_repo_file(expected_diff_file, "\n".join(diff_result))
