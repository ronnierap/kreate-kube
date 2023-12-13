import importlib.metadata
import inspect
import logging
import os
import re
import warnings
from collections.abc import MutableMapping

from . import _jinyaml, Komponent, Konfig
from ._app import App
from ._cli import Cli
from ._core import pprint_map, pprint_tuple, print_filtered
from ._kontext import Module, VersionWarning, load_class
from ._repo import clear_cache


FORMAT = "%(message)s"
logger = logging.getLogger(__name__)


def argument(*name_or_flags, **kwargs):
    """Convenience function to properly format arguments to pass to the
    subcommand decorator.
    """
    return (list(name_or_flags), kwargs)


class KoreModule(Module):
    def init_cli(self, cli: Cli):
        # cli.add_help_section("kore commands:")
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
            metavar="file",
            action="store",
            default=None,
            help="konfig file or directory to use (default=KREATE_MAIN_KONFIG_PATH or .)",
        )
        cli.parser.add_argument(
            "-d",
            "--define",
            metavar="yaml-setting",
            action="append",
            default=[],
            help="add yaml (toplevel) element to konfig file",
        )
        cli.parser.add_argument(
            "-i",
            "--inklude",
            metavar="path",
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
            "-W",
            "--warn-filter",
            action="append",
            metavar="filter",
            help="set python warnings filter",
            default=[],
        )

    def process_kore_options(self, args):
        if args.local_repo:
            os.environ["KREATE_REPO_USE_LOCAL_DIR"] = "True"
        if args.quiet:
            warnings.filterwarnings("ignore")
            # logging.basicConfig(format="%(message)s", level=logging.ERROR)
            logging.basicConfig(format=FORMAT, level=logging.WARN)
        elif args.verbose >= 3:
            logging.basicConfig(level=5)
        elif args.verbose == 2:
            logging.basicConfig(level=logging.DEBUG)
            _jinyaml.logger.setLevel(logging.INFO)
        elif args.verbose == 1:
            logging.basicConfig(format=FORMAT, level=logging.VERBOSE)
        else:
            logging.basicConfig(format=FORMAT, level=logging.INFO)
        warnings.simplefilter("always", VersionWarning)
        for warn_setting in args.warn_filter:
            self.parse_warning_setting(warn_setting)

    def parse_warning_setting(self, warn_setting: str):
        if warn_setting == "reset":
            warnings.resetwarnings()
            return
        action, message, cat_name, module, lineno = (
            warn_setting.split(":") + [None] * 5
        )[:5]
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


def view_template(cli: Cli, app: App, klass_name: str):
    if klass_name not in app.klasses:
        logger.warning(f"Unknown klass {klass_name}")
        return
    klass = app.klasses[klass_name]
    template_loc = klass.info.get("template")
    if template_loc:
        lines = []
        app.konfig.jinyaml.load_with_jinja_includes(template_loc, lines)
        tmpl_text = "\n".join(lines)
    if cli.args.quiet:
        print(tmpl_text)
    else:
        print("==========================")
        print(f"{klass_name} " f"{klass.python_class.__name__}: " f"{klass.info}")
        print("==========================")
        if klass.python_class.__doc__:
            print(inspect.cleandoc(klass.python_class.__doc__))
        if template_loc:
            print("==========================")
            print("=== Template ===")
            print(tmpl_text)
            print("==========================")
            print("=== Fields ===")
            fields = re.findall("{{ *my.field.[^}]*}}", tmpl_text)
            for field in sorted(set(fields)):
                print(field.replace("{", " ").replace("}", " "))
            print("==========================")
            print("=== Optionals ===")
            fields = re.findall("{{ *my.optional\(['\"]([a-zA-Z_0-9]*)['\"]\)", tmpl_text)
            for field in sorted(set(fields)):
                print(field)
        if doc_loc := klass.info.get("doc"):
            doc = app.konfig.load_repo_file(doc_loc)
            if doc:
                print("==========================")
                print("=== doc ===")
                print(doc)


def view_templates(cli: Cli, templates):
    """view the defintion for a specific klass"""
    # we call the kreate_app method and not the convenience app()
    # method, because aktivating the app, will do stuff that might break
    # template = cli.args.template
    app = App(cli.kreate_konfig())
    if templates:
        for t in templates:
            view_template(cli, app, t)
    else:
        for name, klass in app.klasses.items():
            print(
                f"{name:24} "
                f"{klass.python_class.__name__:20} "
                f"{klass.info.get('template', 'no template')}"
            )


def view_aliases():
    return {
        "i": "inklude",
        "s": "strukt",
        "a": "app",
        "t": "template",
        "wf": "warningfilters",
        "tmpl": "template",
        "ink": "inklude",
        "p": "paths",
        "path": "paths",
        "y": "yaml",
        "k": "komponent",
        "komp": "komponent",
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
    """view the entire konfig or subkey(s); possible other subcommand arguments: [template, warningfilters, alias]"""
    print_full_config = True
    yaml_mode = True
    if cli.params:
        for idx, param in enumerate(cli.params):
            param = view_aliases().get(param, param)

            # Check for View-Parameters
            if param == "paths":
                # Change to property view
                yaml_mode = False
                continue
            elif param == "yamlview":
                yaml_mode = True
                continue

            # Regular Parameters
            if not cli.args.quiet:
                print(f"==== view {param} =======")
            print_full_config = False
            if param == "template":
                # View Templates
                view_templates(cli, cli.params[idx + 1 :])
                break

            elif param == "komponent":
                # View komponent details
                view_komponent(cli, cli.params[idx + 1])
                break

            elif param == "warningfilters":
                # View Warning Filter
                view_warning_filters()

            elif param == "alias":
                # View Alassses
                for alias, full in view_aliases().items():
                    print(f"{alias:8} {full}")

            else:
                # View Filtered Section
                konfig = cli.kreate_konfig()

                # Get search path and pattern
                if "=" in param:
                    path, pattern = param.split("=", 1)
                else:
                    path = param
                    pattern = None

                logger.info(f"Pattern: {pattern}")
                result = konfig.get_path(path)
                if yaml_mode:
                    if isinstance(result, str):
                        print(f"{path}: {result}")
                    else:
                        print(f"{path}:")
                        pprint_map(result, indent="  ")
                else:
                    if isinstance(result, str):
                        print_filtered(f"{path}={result}", pattern)
                    else:
                        logger.info("flatten dict found")
                        pprint_tuple(
                            __flatten_dict(result).items(),
                            prefix=path,
                            pattern=pattern,
                        )
            print()

    if print_full_config:
        konfig = cli.kreate_konfig()
        if yaml_mode:
            pprint_map(konfig.yaml)
        else:
            pprint_tuple(__flatten_dict(konfig.dict_).items())


def view_warning_filters():
    for w in warnings.filters:
        print(w)


def view_komponent(cli: Cli, komp_id: str):
    app = cli.kreate_files()
    komp: Komponent = app.komponents_by_id[komp_id]
    print(komp.id, komp.klass)
    print("=== Strukture ===")
    pprint_map(komp.strukture)
    # if isinstance(komp.klass.python_class, JinjaKomponent):
    template_loc = komp.klass.info.get("template")
    if template_loc:
        lines = []
        app.konfig.jinyaml.load_with_jinja_includes(template_loc, lines)
        tmpl_text = "\n".join(lines)
        #tmpl_text = app.konfig.load_repo_file(template_loc)
        print("=== Fields ===")
        fields = re.findall("{{ *my.field.([a-zA-Z_0-9]*)", tmpl_text)
        for field in sorted(set(fields)):
            print(f"  {field}: " + str(komp._field(field, "**not-set**")))
            if cli.args.verbose > 0:
                found = False
                found = _pfp(app.konfig, f"strukt.{komp.id}.{field}", found)
                found = _pfp(app.konfig, f"strukt.field.{komp.id}.{field}", found)
                found = _pfp(app.konfig, f"val.{komp.id}.{field}", found)
                found = _pfp(app.konfig, f"val.field.{komp.id}.{field}", found)
                found = _pfp(app.konfig, f"val.{komp.klass.name}.{field}", found)
                found = _pfp(app.konfig, f"val.field.{komp.klass.name}.{field}", found)
                found = _pfp(app.konfig, f"val.generic.{field}", found)
                found = _pfp(app.konfig, f"val.field.generic.{field}", found)
        fields = re.findall("{{ *my.optional\(['\"]([a-zA-Z_0-9]*)['\"]\)", tmpl_text)
        print("=== Optionals ===")
        for field in sorted(set(fields)):
            print(f"  {field}: " + str(komp._field(field, "**not-set**")))
            if cli.args.verbose > 0:
                found = False
                found = _pfp(app.konfig, f"strukt.{komp.id}.{field}", found)
                found = _pfp(app.konfig, f"strukt.field.{komp.id}.{field}", found)
                found = _pfp(app.konfig, f"val.{komp.id}.{field}", found)
                found = _pfp(app.konfig, f"val.field.{komp.id}.{field}", found)
                found = _pfp(app.konfig, f"val.{komp.klass.name}.{field}", found)
                found = _pfp(app.konfig, f"val.field.{komp.klass.name}.{field}", found)
                found = _pfp(app.konfig, f"val.generic.{field}", found)
                found = _pfp(app.konfig, f"val.field.generic.{field}", found)


def _pfp(konfig: Konfig, path: str, found: bool) -> bool:
    result = konfig.get_path(path)
    if result is None and not found:
        print(f"    . {path}: -")
    elif not found:
        print(f"    * {path}: {result}")
        found = True
    else:
        print(f"      {path}: {result}")
    return found


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
    cmd = cli.params[0]
    app = cli.kreate_files()
    print(cli.run_command(app, cmd))


def shell(cli: Cli):
    """run one or more shell command including pipes"""
    cmd = " ".join(cli.args.script)
    cli.run_shell(cmd)


def __flatten_dict_gen(d, parent_key, sep):
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            yield from __flatten_dict(v, new_key, sep=sep).items()
        else:
            yield new_key, v


def __flatten_dict(d: MutableMapping, parent_key: str = "", sep: str = "."):
    return dict(__flatten_dict_gen(d, parent_key, sep))
