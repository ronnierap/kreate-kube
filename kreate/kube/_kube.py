import logging
import os
import logging
import difflib

from ..krypt import krypt_functions
from ..kore import Kontext, Module, Konfig, App, Cli

logger = logging.getLogger(__name__)

class KubeModule(Module):
    def init_kontext(self, kontext: Kontext) -> None:
        super().init_kontext(kontext)
        kontext.packages.append("kreate-kube")

    def init_cli(self, cli: Cli):
        cli.add_help_section("kube commands:")
        cli.add_subcommand(build, aliases=["b"])
        cli.add_subcommand(diff, aliases=["d"])
        cli.add_subcommand(apply, aliases=["a"])
        cli.add_help_section("test commands:")
        cli.add_subcommand(test, aliases=["t"])
        cli.add_subcommand(test_update, aliases=["tu"])
        cli.add_subcommand(test_diff, aliases=["td"])
        cli.add_subcommand(test_diff_update, aliases=["tdu"])

def build(cli: Cli) -> None:
    """output all the resources"""
    app = cli.kreate_files()
    print(cli.run_command(app, "build"))


def diff(cli: Cli) -> None:
    """diff with current existing resources"""
    app = cli.kreate_files()
    result = cli.run_command(app, "diff", success_codes=(0,1))
    if not result:
        logger.info("no differences found with cluster")
    else:
        logger.info("kreated files differ from cluster")
        print(result)

def apply(cli: Cli) -> None:
    """apply the output to kubernetes"""
    app = cli.kreate_files()
    print(cli.run_command(app, "apply"))


def expected_output_location(konfig: Konfig) -> str:
    loc = os.getenv("KREATE_TEST_EXPECTED_OUTPUT_LOCATION")
    loc = loc or konfig.get_path("tests.expected_output_location")
    loc = loc or "cwd:tests/expected-output-{konfig.app.appname}-{konfig.app.env}.out"
    loc = loc.format(konfig=konfig.yaml)
    return loc


def expected_diff_location(konfig: Konfig) -> str:
    loc = os.getenv("KREATE_TEST_EXPECTED_DIFF_LOCATION")
    loc = loc or konfig.get_path("tests.expected_diff_location")
    loc = loc or "cwd:tests/expected-diff-{konfig.app.appname}-{konfig.app.env}.out"
    loc = loc.format(konfig=konfig.yaml)
    return loc


def build_output(cli: Cli, app: App) -> str:
    # Do not dekrypt secrets for testing
    krypt_functions._dekrypt_testdummy = True
    return cli.run_command(app, "build")

def truncate_ignores(ignores, lines):
    for idx, line in enumerate(lines):
        for ign in ignores:
            if ign in line:
                line = line.split(ign)[0] + ign + " ... "
                logger.info(f"ignoring part after: {line}")
            lines[idx] = line
    return lines



def test_result(cli: Cli, app: App, n=0):
    ignores = [] # cli.konfig().get_path("tests.ignore", [])
    build_lines = build_output(cli, app).splitlines()
    loc = expected_output_location(app.konfig)
    expected_lines = app.konfig.load_repo_file(loc).splitlines()
    diff = difflib.unified_diff(
        truncate_ignores(ignores, expected_lines),
        truncate_ignores(ignores, build_lines),
        fromfile="expected-output",
        tofile="kreated-output",
        n=n,
    )
    return [line.strip() for line in diff]


def test(cli: Cli) -> None:
    """test output against expected-output-<app>-<env>.out file"""
    krypt_functions._dekrypt_testdummy = True
    app = cli.kreate_files()
    diff_result = test_result(cli, app)
    for line in diff_result:
        print(line)


def test_update(cli: Cli) -> None:
    """update expected-output-<app>-<env>.out file with new output"""
    krypt_functions._dekrypt_testdummy = True
    app = cli.kreate_files()
    loc = expected_output_location(app.konfig)
    app.konfig.save_repo_file(loc, build_output(cli, app))


def test_diff(cli: Cli):
    """test output against expected-diff-<app>-<env>.out file"""
    krypt_functions._dekrypt_testdummy = True
    app = cli.kreate_files()
    diff_result = test_result(cli, app)
    loc = expected_diff_location(app.konfig)
    expected_diff_lines = app.konfig.load_repo_file(loc).splitlines()
    diff2 = difflib.unified_diff(
        expected_diff_lines,
        diff_result,
        fromfile="expected-diff",
        tofile="kreated-diff",
        n=0,
    )
    for line in diff2:
        print(line.strip())


def test_diff_update(cli: Cli) -> None:
    """update expected-diff-<app>-<env>.out file with new diff"""
    krypt_functions._dekrypt_testdummy = True
    app = cli.kreate_files()
    diff_result = test_result(cli, app)
    loc = expected_diff_location(app.konfig)
    app.konfig.save_repo_file(loc, "\n".join(diff_result))
