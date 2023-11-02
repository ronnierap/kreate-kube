import os
import sys
import shutil
import argparse
import logging
import traceback
import inspect
import warnings

from ._core import pprint_map, wrap
from ._repo import clear_cache
from ._konfig import VersionWarning

from . import _jinyaml
from ._app import App, Konfig
from ._jinja_app import JinjaApp, load_class
from pathlib import Path
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
        self._konfig = None
        self._app = None
        self.formatwarnings_orig = warnings.formatwarning
        warnings.formatwarning = self.custom_warn_format
        self.load_dotenv()
        self.epilog = "subcommands:\n"
        self.cli = argparse.ArgumentParser(
            prog="kreate",
            usage=(
                "kreate [optional arguments] <konfig> [<subcommand>] [subcommand options]"
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

    def default_command(self):
        files(self)

    def custom_warn_format(self, msg, cat, filename, lineno, line):
        #if cat is UserWarning or cat is VersionWarning:
            return f'WARNING: {msg}\n'
        #return self.formatwarnings_orig(msg, cat, filename, lineno, line)

    def get_packages(self):
        """a list of packages that are shown in the version command"""
        return []

    def calc_dict(self):
        result = {}
        for d in self.args.define:
            k, v = d.split("=", 1)
            wrap(result).set(k, v)
        return result

    def konfig(self):
        if not self._konfig:
            self._konfig = self.kreate_konfig(self.konfig_filename)
            self._konfig.check_kreate_version()
        return self._konfig

    def app(self):
        if not self._app:
            self._app = self.kreate_app()
        return self._app

    def kreate_konfig(self, filename: str) -> Konfig:
        return Konfig(filename, dict_=self.calc_dict(), inkludes=self.args.inklude)

    def kreate_app(self) -> App:
        return App(self.konfig())

    def add_subcommands(self):
        cmd = self.add_subcommand(files, [], aliases=["f"])

        cmd = self.add_subcommand(command, [], aliases=["cmd"])
        cmd.add_argument("cmd", help="command to run", action="store", default=[])

        cmd = self.add_subcommand(shell, [], aliases=["sh"])
        cmd.add_argument("script", help="command(s) to run", nargs=argparse.REMAINDER)

        self.add_subcommand(clear_repo_cache, [], aliases=["cc"])
        # subcommand: version
        self.add_subcommand(version, [], aliases=["vr"])
        # subcommand: view
        cmd = self.add_subcommand(view, [], aliases=["v"])
        cmd.add_argument("key", help="key(s) to show", action="store", nargs="*")
        # self.add_output_options(cmd)

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
        load_dot_env = True
        load_kreate_env = True
        for arg in sys.argv:
            if arg == "--no-dotenv":
                load_dot_env = False
            if arg == "--no-kreate-env":
                load_kreate_env = False
        try:
            if load_dot_env:
                dotenv.load_env(Path.cwd() / ".env")
            if load_kreate_env:
                dotenv.load_env(Path.home() / ".config/kreate/kreate.env")
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
                print(
                    f"DEBUG:prepending KREATE_OPTIONS to get {result}", file=sys.stderr
                )
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
                if isinstance(e, Warning):
                    # With a warning it might not be clear that the warning is due to a
                    print(f"stopping due to {type(e).__name__}: {e}")
                    print(f"  use -W default::{e.__class__.__name__} to override this")
                    print(f"  possibly define this as export KREATE_OPTIONS or in .env file")
                else:
                    print(f"{type(e).__name__}: {e}")
            sys.exit(1)
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

    def add_konfig_options(self, cmd):
        cmd.add_argument(
            "-k",
            "--konfig",
            metavar='file',
            action="store",
            default=None,
            help="konfig file or directory to use (default=KREATE_MAIN_KONFIG_PATH or .)",
        )
        cmd.add_argument(
            "-d",
            "--define",
            metavar='yaml-setting',
            action="append",
            default=[],
            help="add yaml (toplevel) element to konfig file",
        )
        cmd.add_argument(
            "-i",
            "--inklude",
            metavar='path',
            action="append",
            default=[],
            help="inklude extra files before parsing main konfig",
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
            "-W", "--warn-filter", action="append", metavar="filter", help="set python warnings filter", default=[],
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
            "--no-dotenv",
            action="store_true",
            help="do not load .env file from working dir",
        )
        self.cli.add_argument(
            "--no-kreate-env",
            action="store_true",
            help="do not load kreate.env file from user home .config dir",
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
            warnings.filterwarnings("ignore")
            logging.basicConfig(format="%(message)s", level=logging.ERROR)
        else:
            logging.basicConfig(format="%(message)s", level=logging.WARN)
        warnings.simplefilter("error", VersionWarning)
        for warn_setting in args.warn_filter:
            self.parse_warning_setting(warn_setting)
        self.konfig_filename = args.konfig

    def parse_warning_setting(self, warn_setting: str):
        if warn_setting == "reset":
            warnings.resetwarnings()
            return
        action, message, cat_name, module, lineno = (warn_setting.split(":") + [None]*5)[:5]
        message = message or ""
        if cat_name is None or cat_name == "":
            category = Warning
        elif cat_name == "VersionWarning":
            category = VersionWarning
        else:
            category = load_class(cat_name)
        module = module or ""
        lineno = lineno or 0
        warnings.filterwarnings(action, message, category, module, lineno)

    def kreate_files(self):
        app: App = self.app()
        app.kreate_komponents()
        app.kreate_files()

    def run_shell(self, cmd: str) -> None:
        self.kreate_files()
        cmd = cmd.format(app=self.app(), konf=self.konfig(), cli=self)
        logger.info(f"running: {cmd}")
        os.system(cmd)

    def run_command(self, cmd_name: str, default_command: str = None) -> None:
        cmd : str = self.konfig().get_path(f"system.command.{cmd_name}", default_command)
        self.run_shell(cmd)




def clear_repo_cache(cli: KoreCli):
    """clear the repo cache"""
    clear_cache()


def view_template(cli, template):
    app: JinjaApp = cli.kreate_app()
    if template not in app.kind_templates or template not in app.kind_classes:
        logger.warning(f"Unknown template kind {template}")
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


def view_templates(cli, templates):
    """view the template for a specific kind"""
    # we call the kreate_app method and not the convenience app()
    # method, because aktivating the app, will do stuff that might break
    # template = cli.args.template
    if templates:
        for t in templates:
            view_template(cli, t)
    else:
        app: JinjaApp = cli.kreate_app()
        for template in app.kind_templates:
            if template in app.kind_templates and template in app.kind_classes:
                print(
                    f"{template:24} "
                    f"{app.kind_classes[template].__name__:20} "
                    f"{app.kind_templates[template]}"
                )
            else:
                logger.warning(f"skipping template {template}")


def view_aliases():
    return {
        "i": "inklude",
        "s": "strukt",
        "a": "app",
        "t": "template",
        "wf": "warningfilters",
        "tmpl": "template",
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
    first = True
    if cli.args.key:
        for idx, k in enumerate(cli.args.key):
            k = view_aliases().get(k, k)
            print(f"==== view {k} =======")
            if k == "template":
                view_templates(cli, cli.args.key[idx + 1 :])
                break
            elif k == "warningfilters":
                view_warning_filters()
            elif k == "alias":
                for alias, full in view_aliases().items():
                    print(f"{alias:8} {full}")
            else:
                result = konfig.get_path(k)
                if isinstance(result, str):
                    print(f"{k}: {result}")
                else:
                    print(k + ":")
                    pprint_map(result, indent="  ")
            print()
    else:
        pprint_map(konfig.yaml)

def view_warning_filters():
    for w in warnings.filters:
        print(w)

def version(cli: KoreCli):
    """view the version"""
    for pckg in cli.get_packages():
        try:
            version = cli.dist_package_version(pckg)
        except importlib.metadata.PackageNotFoundError:
            version = "Unknown"
        print(f"{pckg}: {version}")

def files(cli: KoreCli) -> None:
    """kreate all the files (default command)"""
    cli.kreate_files()

def command(cli: KoreCli):
    """run a predefined command from system.command"""
    cmd = cli.args.cmd
    cli.run_command(cmd)

def shell(cli: KoreCli):
    """run one or more shell command including pipes"""
    cmd = " ".join(cli.args.script)
    cli.run_shell(cmd)
