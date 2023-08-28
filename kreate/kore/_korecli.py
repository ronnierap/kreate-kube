import os
import sys
import shutil
import argparse
import logging
import traceback
import inspect
from jinja2 import TemplateError
from sys import exc_info

from . import _jinyaml
from ._app import App, Konfig
from ._jinja_app import JinjaApp
from ._jinyaml import load_data, yaml_dump
import importlib.metadata

logger = logging.getLogger(__name__)


def argument(*name_or_flags, **kwargs):
    """Convenience function to properly format arguments to pass to the
    subcommand decorator.
    """
    return (list(name_or_flags), kwargs)


class KoreCli:
    def __init__(self):
        self._konfig = None
        self._app = None
        self.epilog = "subcommands:\n"
        self.cli = argparse.ArgumentParser(
            prog="kreate",
            usage=(
                "kreate [optional arguments] [<subcommand>] [subcommand"
                " options]"
            ),
            description=(
                "kreates files for deploying applications on kubernetes"
            ),
            formatter_class=argparse.RawTextHelpFormatter,
        )
        self.subparsers = self.cli.add_subparsers(
            # title="subcmd",
            # description="valid subcommands",
            dest="subcommand",
            metavar="see subcommands",
        )
        self.add_subcommands()

    def get_packages(self):
        return []

    def konfig(self):
        if not self._konfig:
            self._konfig = self._kreate_konfig(self.konfig_filename)
            self._tune_konfig()
            if not self.args.skip_requires:
                self._konfig.check_requires()
        return self._konfig

    def app(self):
        if not self._app:
            self._app = self._kreate_app()
            self._tune_app()
        return self._app

    def _kreate_konfig(self, filename: str) -> Konfig:
        return Konfig(filename)

    def _kreate_app(self) -> App:
        return App(self.konfig())

    def _tune_konfig(self) -> None:
        pass

    def _tune_app(self) -> None:
        self._app.kreate_komponents_from_strukture()
        self._app.aktivate()

    def add_subcommands(self):
        # subcommand: version
        self.add_subcommand(version, [], aliases=["vr"])
        # subcommand: view_strukture
        cmd = self.add_subcommand(view_strukture, [], aliases=["vs"])
        cmd.add_argument(
            "-k",
            "--komp",
            help="komponent to show",
            action="store",
            default=None,
        )
        # subcommand: view defaults
        cmd = self.add_subcommand(view_defaults, [], aliases=["vd"])
        cmd.add_argument(
            "-k",
            "--komp",
            help="komponent to show",
            action="store",
            default=None,
        )
        # subcommand: view_values
        cmd = self.add_subcommand(view_values, [], aliases=["vv"])
        # subcommand: view_template
        cmd = self.add_subcommand(view_template, [], aliases=["vt"])
        cmd.add_argument(
            "-t",
            "--template",
            help="template to show",
            action="store",
            default=None,
        )
        # subcommand: view_konfig
        cmd = self.add_subcommand(view_konfig, [], aliases=["vk"])
        cmd.add_argument("-k", "--kind", action="store", default=None)
        # subcommand: requirements
        cmd = self.add_subcommand(requirements, [], aliases=["rq"])

    def dist_package_version(self, package_name: str):
        return importlib.metadata.version(package_name)

    def add_subcommand(self, func, args=[], aliases=[], parent=None):
        parent = parent or self.subparsers
        alias0 = aliases[0] if aliases else ""
        self.epilog += (
            f"  {func.__name__:14}    {alias0 :3} {func.__doc__ or ''} \n"
        )
        parser = parent.add_parser(
            func.__name__, aliases=aliases, description=func.__doc__
        )
        for arg in args:
            parser.add_argument(*arg[0], **arg[1])
        parser.set_defaults(func=func)
        return parser

    def run(self):
        self.cli.epilog = self.epilog + "\n"
        self.add_main_options()
        self.args = self.cli.parse_args()
        self.process_main_options(self.args)
        try:
            if self.args.subcommand is None:
                self.default_command()
            else:
                self.args.func(self)
        except Exception as e:
            if self.args.verbose:
                traceback.print_exc()
            else:
                print(f"{type(e).__name__}: {e}")
            if _jinyaml._current_jinja_file:
                lineno = jinja2_template_error_lineno()
                print(
                    "while processing template "
                    f"{_jinyaml._current_jinja_file}:{lineno}"
                )
        finally:
            if not self.args.keep_secrets:
                if self._konfig:
                    # konfig was kreated so secrets might need to be cleaned
                    konfig = self.konfig()
                    dir = konfig.target_dir
                    secrets_dir = f"{dir}/secrets"
                    if os.path.exists(secrets_dir):
                        logger.info(
                            f"removing {secrets_dir}, "
                            "use --keep-secrets or -K option to keep it"
                        )
                        shutil.rmtree(secrets_dir)

    def default_command(self):
        version(self)

    def add_main_options(self):
        self.cli.add_argument(
            "-k",
            "--konf",
            action="store",
            default=".",
            help="konfig file or directory to use (default=.)",
        )
        self.cli.add_argument(
            "-v",
            "--verbose",
            action="count",
            default=0,
            help="output more details (inluding stacktrace) -vv even more",
        )
        self.cli.add_argument(
            "-w", "--warn", action="store_true", help="only output warnings"
        )
        self.cli.add_argument(
            "-q",
            "--quiet",
            action="store_true",
            help="do not output any info, just essential output",
        )
        self.cli.add_argument(
            "-K",
            "--keep-secrets",
            action="store_true",
            help="do not remove secrets dirs",
        )
        self.cli.add_argument(
            "-R",
            "--skip-requires",
            action="store_true",
            help="do not check if required dependency versions are installed",
        )

    def process_main_options(self, args):
        if args.verbose >= 2:
            logging.basicConfig(level=logging.DEBUG)
        elif args.verbose == 1:
            logging.basicConfig(level=logging.DEBUG)
            _jinyaml.logger.setLevel(logging.INFO)
        elif args.warn:
            logging.basicConfig(format="%(message)s", level=logging.WARN)
        elif args.quiet:
            logging.basicConfig(format="%(message)s", level=logging.ERROR)
        else:
            logging.basicConfig(format="%(message)s", level=logging.INFO)
        self.konfig_filename = args.konf


def view_strukture(cli: KoreCli):
    """view the application strukture"""
    konfig: Konfig = cli.konfig()
    konfig.calc_strukture().pprint(field=cli.args.komp)


def view_defaults(cli: KoreCli):
    """view the application strukture defaults"""
    konfig: Konfig = cli.konfig()
    konfig.calc_strukture().default.pprint(field=cli.args.komp)


def view_template(cli: KoreCli):
    """view the template for a specific kind"""
    # we call the _kreate_app method and not the convenience app()
    # method, because aktivating the app, will kopy_files
    app: JinjaApp = cli._kreate_app()
    template = cli.args.template
    if template:
        if (
            template not in app.kind_templates
            or template not in app.kind_classes
        ):
            logger.warn(f"Unknown template kind {template}")
            return
        if not cli.args.quiet:
            print("==========================")
            print(
                f"{template} "
                f"{app.kind_classes[template].__name__}: "
                f"{app.kind_templates[template]}"
            )
            print("==========================")
            if app.kind_classes[template].__doc__:
                print(inspect.cleandoc(app.kind_classes[template].__doc__))
                print("==========================")
        if app.kind_templates[template].filename != "NoTemplate":
            print(load_data(app.kind_templates[template]))
    else:
        for template in app.kind_templates:
            if template in app.kind_templates and template in app.kind_classes:
                print(
                    f"{template:24} "
                    f"{app.kind_classes[template].__name__:20} "
                    f"{app.kind_templates[template]}"
                )
            else:
                logger.debug("skipping kind")


def view_values(cli: KoreCli):
    """view the application values"""
    konfig: Konfig = cli.konfig()
    for k, v in konfig.values.items():
        print(f"{k}: {v}")


def view_konfig(cli: KoreCli):
    """view the application konfig file (with defaults)"""
    konfig: Konfig = cli.konfig()
    if "krypt_key" in konfig.yaml:
        konfig.yaml["krypt_key"] = "censored"
    yaml_dump(konfig.yaml, sys.stdout)


def requirements(cli: KoreCli):
    """view the listed requirements"""
    konfig: Konfig = cli.konfig()
    for line in konfig.get_requires():
        print(line)


def version(cli: KoreCli):
    """view the version"""
    for pckg in cli.get_packages():
        try:
            version = cli.dist_package_version(pckg)
        except importlib.metadata.PackageNotFoundError:
            version = "Unknown"
        print(f"{pckg}: {version}")


def jinja2_template_error_lineno():
    type, value, tb = exc_info()
    if not issubclass(type, TemplateError):
        return None
    if hasattr(value, "lineno"):
        # in case of TemplateSyntaxError
        return value.lineno
    while tb:
        # print(tb.tb_frame.f_code.co_filename, tb.tb_lineno)
        if tb.tb_frame.f_code.co_filename == "<template>":
            return tb.tb_lineno
        tb = tb.tb_next
