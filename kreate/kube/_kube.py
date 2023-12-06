import difflib
import io
import logging
import os
import re
from pathlib import Path

import yaml

from .resource import CustomResource
from ..kore import Kontext, Module, Konfig, App, Cli
from ..krypt import krypt_functions

logger = logging.getLogger(__name__)


class KubeModule(Module):
    def init_kontext(self, kontext: Kontext) -> None:
        kontext.packages.append("kreate-kube")

    def init_cli(self, cli: Cli):
        cli.add_help_section("kube commands:")
        cli.add_subcommand(build, aliases=["b"])
        cli.add_subcommand(diff, aliases=["d"])
        cli.add_subcommand(vardiff)
        cli.add_subcommand(apply, aliases=["a"])
        cli.add_help_section("test commands:")
        cli.add_subcommand(test, aliases=["t"])
        cli.add_subcommand(test_update, aliases=["tu"])
        cli.add_subcommand(test_diff, aliases=["td"])
        cli.add_subcommand(test_diff_update, aliases=["tdu"])

    def init_app(self, app: App) -> None:
        app.register_klass(CustomResource)


def build(cli: Cli) -> None:
    """output all the resources"""
    app = cli.kreate_files()
    print(cli.run_command(app, "build"))


def diff(cli: Cli) -> None:
    """diff with current existing resources"""
    app = cli.kreate_files()
    result = cli.run_command(app, "diff", success_codes=(0, 1))
    if not result:
        logger.info("no differences found with cluster")
    else:
        logger.info("kreated files differ from cluster")
        print(result)



def vardiff(cli: Cli) -> None:
    """vardiff with current existing resources"""
    app = cli.kreate_files()
    for comp in app.komponents:
        print(f"  {comp.get_filename()} {comp.klass.python_class} {comp.klass.name} {comp.name}")

    build_result = cli.run_command(app, "build")

    documents = app.konfig.jinyaml.yaml_parser.load_all(build_result)
    for target_doc in documents:
        if target_doc["kind"] in ('ConfigMap', 'Secret'):
            metadata_name = target_doc["metadata"]["name"]
            pattern = r".+-[a-z0-9]{10}$"
            hash_found = re.search(pattern, metadata_name)
            # Check correct label
            resource_name = ""
            label_filter = ""
            if target_doc["kind"] == "ConfigMap" and hash_found:
                label_filter = f"-l config-map={metadata_name[:metadata_name.rfind('-')]}"

                names = cli.run_command(app, "getname", resource_type=target_doc["kind"],
                                        label_filter=label_filter).split('\n')

                # Return youngest one
                resource_name = names[-1].split('/', 2)[1]

            else:
                resource_name = metadata_name

            result = cli.run_command(app, "getyaml", resource_type=target_doc["kind"],
                                     resource_name=resource_name)

            data = yaml.safe_load(result)

            # Remove specified keys
            if 'metadata' in data:
                metadata = data['metadata']
                if 'annotations' in metadata:
                    annotation = metadata['annotations']
                    if 'kubectl.kubernetes.io/last-applied-configuration' in annotation:
                        del annotation['kubectl.kubernetes.io/last-applied-configuration']
                    if not metadata['annotations']:
                        del metadata['annotations']
                if 'creationTimestamp' in metadata:
                    del metadata['creationTimestamp']
                if 'resourceVersion' in metadata:
                    del metadata['resourceVersion']
                if 'uid' in metadata:
                    del metadata['uid']

            # Convert data back to YAML string
            result = yaml.dump(data, default_flow_style=False, width=9999)

            buf = io.BytesIO()
            app.konfig.jinyaml.yaml_parser.dump(target_doc, buf)
            buf_getvalue = buf.getvalue()
            b = str(buf_getvalue, 'UTF-8')

            target_result = yaml.dump(yaml.safe_load(b), default_flow_style=False, width=9999)

            # Compare this target_doc with the resource in Kubernetes
            diff2 = difflib.unified_diff(result.split('\n'), target_result.split('\n'), fromfile="Current",
                                         tofile="Target")
            for line in diff2:
                print(line.strip())


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
    ignores = []  # cli.konfig().get_path("tests.ignore", [])
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
    if Path(loc).exists():
        expected_diff_lines = app.konfig.load_repo_file(loc).splitlines()
    else:
        expected_diff_lines = []
        logger.warning(f"no expected diff file found {loc}")
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
