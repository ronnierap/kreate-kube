import os
import logging
import inspect
import warnings
import importlib.metadata

from ._core import pprint_map, wrap
from ._repo import clear_cache
from ._kontext import Module, VersionWarning, load_class
from ._cli import Cli
from . import _jinyaml
from ._app import App

logger = logging.getLogger(__name__)


def argument(*name_or_flags, **kwargs):
    """Convenience function to properly format arguments to pass to the
    subcommand decorator.
    """
    return (list(name_or_flags), kwargs)


class KoreModule(Module):
    def init_cli(self, cli: Cli):
        #cli.add_help_section("kore commands:")
        self.add_kore_subcommands(cli)
        self.add_kore_options(cli)

    def process_cli_options(self, cli: Cli):
        self.process_kore_options(cli.args)

    def add_kore_subcommands(self, cli: Cli):
        cli.add_subcommand(clear_cache, aliases=["cc"])
        cli.add_subcommand(version, aliases=["vr"])
        cli.add_subcommand(view, aliases=["v"])
        cli.add_subcommand(command, aliases=["cmd"])
        cli.add_subcommand(shell, aliases=["sh"])

    def add_kore_options(self, cli: Cli):
        self.add_output_options(cli)
        self.add_konfig_options(cli)
        cli.parser.add_argument(
            "-K",
            "--keep-secrets",
            action="store_true",
            help="do not remove secrets dirs",
        )
        cli.parser.add_argument(
            "--no-dotenv",
            action="store_true",
            help="do not load .env file from working dir",
        )
        cli.parser.add_argument(
            "--no-kreate-env",
            action="store_true",
            help="do not load kreate.env file from user home .config dir",
        )


    def add_konfig_options(self, cli: Cli):
        cli.parser.add_argument(
            "-k",
            "--konfig",
            metavar='file',
            action="store",
            default=None,
            help="konfig file or directory to use (default=KREATE_MAIN_KONFIG_PATH or .)",
        )
        cli.parser.add_argument(
            "-d",
            "--define",
            metavar='yaml-setting',
            action="append",
            default=[],
            help="add yaml (toplevel) element to konfig file",
        )
        cli.parser.add_argument(
            "-i",
            "--inklude",
            metavar='path',
            action="append",
            default=[],
            help="inklude extra files before parsing main konfig",
        )
        cli.parser.add_argument(
            "-l",
            "--local-repo",
            action="store_true",
            help="use local repo's (force KREATE_REPO_USE_LOCAL_DIR=True)",
        )

    def add_output_options(self, cli: Cli):
        cli.parser.add_argument(
            "-v",
            "--verbose",
            action="count",
            default=0,
            help="output more details (inluding stacktrace) -vv even more",
        )
        cli.parser.add_argument(
            "-w", "--warn", action="store_true", help="only output warnings"
        )
        cli.parser.add_argument(
            "-q",
            "--quiet",
            action="store_true",
            help="do not output any info, just essential output",
        )
        cli.parser.add_argument(
            "-W", "--warn-filter", action="append", metavar="filter", help="set python warnings filter", default=[],
        )

    def process_kore_options(self, args):
        if args.local_repo:
            os.environ["KREATE_REPO_USE_LOCAL_DIR"] = "True"
        if args.quiet:
            warnings.filterwarnings("ignore")
            #logging.basicConfig(format="%(message)s", level=logging.ERROR)
            logging.basicConfig(format="%(message)s", level=logging.WARN)
        elif args.verbose >= 3:
            logging.basicConfig(level=5)
        elif args.verbose == 2:
            logging.basicConfig(level=logging.DEBUG)
            _jinyaml.logger.setLevel(logging.INFO)
        elif args.verbose == 1:
            logging.basicConfig(format="%(message)s", level=logging.VERBOSE)
        else:
            logging.basicConfig(format="%(message)s", level=logging.INFO)
        warnings.simplefilter("error", VersionWarning)
        for warn_setting in args.warn_filter:
            self.parse_warning_setting(warn_setting)

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


def clear_repo_cache(cli: Cli):
    """clear the repo cache"""
    clear_cache()


def view_template(cli: Cli, template: str):
    app = App(cli.kreate_konfig())
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


def view_templates(cli: Cli, templates):
    """view the template for a specific kind"""
    # we call the kreate_app method and not the convenience app()
    # method, because aktivating the app, will do stuff that might break
    # template = cli.args.template
    if templates:
        for t in templates:
            view_template(cli, t)
    else:
        app = App(cli.kreate_konfig())
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

def view(cli: Cli):
    """view the entire konfig or subkey(s)"""
    first = True
    if cli.params:
        for idx, k in enumerate(cli.params):
            k = view_aliases().get(k, k)
            print(f"==== view {k} =======")
            if k == "template":
                view_templates(cli, cli.params[idx + 1 :])
                break
            elif k == "warningfilters":
                view_warning_filters()
            elif k == "alias":
                for alias, full in view_aliases().items():
                    print(f"{alias:8} {full}")
            else:
                konfig = cli.kreate_konfig()
                result = konfig.get_path(k)
                if isinstance(result, str):
                    print(f"{k}: {result}")
                else:
                    print(k + ":")
                    #print(wrap(result).pprint_str(indent="  "))
                    pprint_map(result, indent="  ")
            print()
    else:
        konfig = cli.kreate_konfig()
        pprint_map(konfig.yaml)

def view_warning_filters():
    for w in warnings.filters:
        print(w)

def version(cli: Cli):
    """view the version"""
    for pckg in cli.kontext.packages:
        try:
            version = cli.dist_package_version(pckg)
        except importlib.metadata.PackageNotFoundError:
            version = "Unknown"
        print(f"{pckg}: {version}")


def command(cli: Cli):
    """run a predefined command from system.command"""
    cmd = cli.args.cmd
    print(cli.run_command(cmd))

def shell(cli: Cli):
    """run one or more shell command including pipes"""
    cmd = " ".join(cli.args.script)
    cli.run_shell(cmd)
