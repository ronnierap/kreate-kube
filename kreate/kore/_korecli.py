import os
import sys
import shutil
import argparse
import logging
import traceback
import inspect

from ._core import pprint_map, wrap
from ._repo import clear_cache

from . import _jinyaml
from ._app import App, Konfig
from ._jinja_app import JinjaApp
import importlib.metadata
import kreate.kore.dotenv as dotenv

logger = logging.getLogger(__name__)


def argument(*name_or_flags, **kwargs):
    """Convenience function to properly format arguments to pass to the
    subcommand decorator.
    """
    return (list(name_or_flags), kwargs)


class KoreCli:
    def __init__(self):
        self.load_dotenv()
        self._konfig = None
        self._app = None
        self.epilog = "subcommands:\n"
        self.cli = argparse.ArgumentParser(
            prog="kreate",
            usage=(
                "kreate [optional arguments] [<subcommand>] [subcommand" " options]"
            ),
            description=("kreates files for deploying applications on kubernetes"),
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
        """a list of packages that are shown in the version command"""
        return []

    def calc_dict(self):
        result = {}
        for d in self.args.define:
            k, v = d.split("=",1)
            wrap(result).set(k, v)
        return result

    def konfig(self):
        if not self._konfig:
            self._konfig = self.kreate_konfig(self.konfig_filename)
            if not self.args.skip_version_check:
                force = self.args.force_version_check
                self._konfig.check_kreate_version(force=force)
        return self._konfig

    def app(self):
        if not self._app:
            self._app = self.kreate_app()
        return self._app

    def kreate_konfig(self, filename: str) -> Konfig:
        return Konfig(filename, dict_ = self.calc_dict(), inkludes=self.args.inklude)

    def kreate_app(self) -> App:
        return App(self.konfig())

    def add_subcommands(self):
        self.add_subcommand(clear_repo_cache, [], aliases=["cc"])

        # subcommand: version
        self.add_subcommand(version, [], aliases=["vr"])
        # subcommand: view
        cmd = self.add_subcommand(view, [], aliases=["v"])
        cmd.add_argument("key", help="key(s) to show", action="store", nargs="*")
        #self.add_output_options(cmd)

        # subcommand: view_template
        cmd = self.add_subcommand(view_template, [], aliases=["vt"])
        cmd.add_argument(
            "-t",
            "--template",
            help="template to show",
            action="store",
            default=None,
        )

    def dist_package_version(self, package_name: str):
        return importlib.metadata.version(package_name)

    def add_subcommand(self, func, args=[], aliases=[], parent=None):
        parent = parent or self.subparsers
        alias0 = aliases[0] if aliases else ""
        self.epilog += f"  {func.__name__:17} {alias0 :3} {func.__doc__ or ''} \n"
        parser = parent.add_parser(
            func.__name__, aliases=aliases, description=func.__doc__
        )
        for arg in args:
            parser.add_argument(*arg[0], **arg[1])
        parser.set_defaults(func=func)
        return parser

    def load_dotenv(self) -> None:
        # Primitive way to check if to load ENV vars before parsing vars
        # .env needs to be loaded before arg parsing, since it may
        # contain KREATE_OPTIONS
        for arg in sys.argv:
            if arg == "--no-dotenv":
                return
        try:
            dotenv.load_dotenv(".env")
        except Exception as e:
            logger.error(
                f"ERROR loading .env file, " f"remove .env file or specify --no-dotenv"
            )
            raise

    def get_argv(self):
        options = os.getenv("KREATE_OPTIONS")
        if options:
            result = [*options.split(), *sys.argv[1:]]
            # options are not parsed yet, so use simple count to
            # determine if it is debug level
            vcount = 0
            for opt in result:
                vcount += 2 if opt.startswith("-vv") else 0
                vcount += 1 if opt == "-v" else 0
            if vcount >= 2:
                print(f"DEBUG:prepending KREATE_OPTIONS to get {result}",
                      file=sys.stderr)
            return result
        return sys.argv[1:]

    def run(self):
        self.cli.epilog = self.epilog + "\n"
        self.add_main_options()
        self.args = self.cli.parse_args(self.get_argv())
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
        finally:
            if not self.args.keep_secrets:
                if self._app:
                    # app was kreated so secrets might need to be cleaned
                    dir = self._app.target_path
                    secrets_dir = f"{dir}/secrets"
                    if os.path.exists(secrets_dir):
                        logger.info(
                            f"removing {secrets_dir}, "
                            "use --keep-secrets or -K option to keep it"
                        )
                        shutil.rmtree(secrets_dir)

    def default_command(self):
        version(self)

    def add_konfig_options(self, cmd):
        cmd.add_argument(
            "-d",
            "--define",
            action="append",
            default=[],
            help="add yaml (toplevel) element to konfig file",
        )
        cmd.add_argument(
            "-i",
            "--inklude",
            action="append",
            default=[],
            help="inklude extra files before parsing main konfig",
        )
        cmd.add_argument(
            "-k",
            "--konf",
            action="store",
            default=".",
            help="konfig file or directory to use (default=.)",
        )

    def add_output_options(self, cmd):
        cmd.add_argument(
            "-v",
            "--verbose",
            action="count",
            default=0,
            help="output more details (inluding stacktrace) -vv even more",
        )
        cmd.add_argument(
            "-w", "--warn", action="store_true", help="only output warnings"
        )
        cmd.add_argument(
            "-q",
            "--quiet",
            action="store_true",
            help="do not output any info, just essential output",
        )

    def add_main_options(self):
        self.add_konfig_options(self.cli)
        self.add_output_options(self.cli)
        self.cli.add_argument(
            "-K",
            "--keep-secrets",
            action="store_true",
            help="do not remove secrets dirs",
        )
        self.cli.add_argument(
            "-C",
            "--skip-version-check",
            action="store_true",
            help="do not check if required version of kreate is used",
        )
        self.cli.add_argument(
            "-F",
            "--force-version-check",
            action="store_true",
            help="force version check even if development version is detected",
        )
        self.cli.add_argument(
            "--no-dotenv",
            action="store_true",
            help="do not load a .env file for working dir",
        )

    def process_main_options(self, args):
        if args.verbose >= 3:
            logging.basicConfig(level=logging.DEBUG)
        elif args.verbose == 2:
            logging.basicConfig(level=logging.DEBUG)
            _jinyaml.logger.setLevel(logging.INFO)
        elif args.verbose == 1:
            logging.basicConfig(format="%(message)s", level=logging.INFO)
        elif args.quiet:
            logging.basicConfig(format="%(message)s", level=logging.ERROR)
        else:
            logging.basicConfig(format="%(message)s", level=logging.WARN)
        self.konfig_filename = args.konf


def clear_repo_cache(cli: KoreCli):
    """clear the repo cache"""
    clear_cache()


def view_template(cli: KoreCli):
    """view the template for a specific kind"""
    # we call the kreate_app method and not the convenience app()
    # method, because aktivating the app, will do stuff that might break
    app: JinjaApp = cli.kreate_app()
    template = cli.args.template
    if template:
        if template not in app.kind_templates or template not in app.kind_classes:
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
        if app.kind_templates[template] != "NoTemplate":
            tmpl = app.kind_templates[template]
            tmpl_text = app.konfig.file_getter.get_data(tmpl)
            print(tmpl_text)
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

def view_aliases():
    return {
        "i": "inklude",
        "s": "strukt",
        "a": "app",
        "ink": "inklude",
        "sys": "system",
        "ver": "version",
        "kust": "strukt.Kustomization",
        "depl": "strukt.Deployment",
        "cron": "strukt.CronJob",
        "ingr": "strukt.Ingress",
        "egr": "strukt.Egress",
        "svc": "strukt.Service",
        "cm": "strukt.ConfigMap",
    }

def view(cli: KoreCli):
    """view the entire konfig or subkey(s)"""
    konfig: Konfig = cli.konfig()
    if cli.args.key:
        for k in cli.args.key:
            k = view_aliases().get(k, k)
            result = konfig.get_path(k)
            if isinstance(result, str):
                print(f"{k}: {result}")
            else:
                print(k + ":")
                pprint_map(result, indent="  ")
    else:
        pprint_map(konfig.yaml)


def version(cli: KoreCli):
    """view the version"""
    for pckg in cli.get_packages():
        try:
            version = cli.dist_package_version(pckg)
        except importlib.metadata.PackageNotFoundError:
            version = "Unknown"
        print(f"{pckg}: {version}")
