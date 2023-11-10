import os
import sys
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
        return KubeKonfig(filename,
                          dict_=self.calc_dict(),
                          inkludes=self.args.inklude,
                          tracer=self.tracer
        )

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


def expected_output_location(cli: KubeCli) -> str:
    loc = os.getenv("KREATE_TEST_EXPECTED_OUTPUT_LOCATION")
    loc = loc or cli.konfig().get_path("tests.expected_output_location")
    loc = loc or "cwd:tests/expected-output-{app.appname}-{app.env}.out"
    loc = loc.format(app=cli.app(), konf=cli.konfig(), cli=cli)
    return loc


def expected_diff_location(cli: KubeCli) -> str:
    loc = os.getenv("KREATE_TEST_EXPECTED_DIFF_LOCATION")
    loc = loc or cli.konfig().get_path("tests.expected_diff_location")
    loc = loc or "cwd:tests/expected-diff-{app.appname}-{app.env}.out"
    loc = loc.format(app=cli.app(), konf=cli.konfig(), cli=cli)
    return loc


def build_output(cli: KubeCli) -> str:
    # Do not dekrypt secrets for testing
    krypt_functions._dekrypt_testdummy = True
    return cli.run_command("build")


def truncate_ignores(ignores, lines):
    for idx, line in enumerate(lines):
        for ign in ignores:
            if ign in line:
                line = line.split(ign)[0] + ign + " ... "
                logger.info(f"ignoring part after: {line}")
            lines[idx] = line
    return lines



def test_result(cli: KubeCli, n=0):
    ignores = cli.konfig().get_path("tests.ignore", [])
    build_lines = build_output(cli).splitlines()
    loc = expected_output_location(cli)
    expected_lines = cli.konfig().load_repo_file(loc).splitlines()
    diff = difflib.unified_diff(
        truncate_ignores(ignores, expected_lines),
        truncate_ignores(ignores, build_lines),
        fromfile="expected-output",
        tofile="kreated-output",
        n=n,
    )
    return [line.strip() for line in diff]


def test(cli: KubeCli) -> None:
    """test output against expected-output-<app>-<env>.out file"""
    diff_result = test_result(cli)
    for line in  diff_result:
        print(line)


def test_update(cli: KubeCli) -> None:
    """test output against expected-output-<app>-<env>.out file"""
    loc = expected_output_location(cli)
    cli.konfig().save_repo_file(loc, build_output(cli))


def test_diff(cli: KubeCli):
    """test output against expected-output-<app>-<env>.out file"""
    diff_result = test_result(cli)
    loc = expected_diff_location(cli)
    expected_diff_lines = cli.konfig().load_repo_file(loc).splitlines()
    diff2 = difflib.unified_diff(
        expected_diff_lines,
        diff_result,
        fromfile="expected-diff",
        tofile="kreated-diff",
        n=0,
    )
    for line in diff2:
        print(line.strip())


def test_diff_update(cli: KubeCli) -> None:
    """update expected-output-<app>-<env>.out file"""
    diff_result = test_result(cli)
    loc = expected_diff_location(cli)
    cli.konfig().save_repo_file(loc, "\n".join(diff_result))
