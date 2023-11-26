import os
import sys
import argparse
import logging
import traceback
import warnings

from ._core import pprint_map, wrap
from ._repo import clear_cache
from ._kontext import VersionWarning

from ._kontext import Kontext
from ._konfig import Konfig
from ._app import App, load_class
from . import _jinyaml
from pathlib import Path
import importlib.metadata
import kreate.kore.dotenv as dotenv

logger = logging.getLogger(__name__)


class Cli:
    def __init__(self, kontext: Kontext):
        self.kontext = kontext
        self.tracer = kontext.tracer
        self.formatwarnings_orig = warnings.formatwarning
        warnings.formatwarning = self.custom_warn_format
        self.epilog = "subcommands:\n"
        self.subcommands = {}
        self.aliases = {}
        self.parser = argparse.ArgumentParser(
            prog="kreate",
            usage=(
                "kreate [options] [<subcommand> [param ...]]"
            ),
            description=("kreates files for deploying applications on kubernetes"),
            formatter_class=argparse.RawTextHelpFormatter,
        )
        self.parser.add_argument("param", nargs="*", help="parameters for subcommand")
        self.add_subcommand(files, aliases=["f"])
        self.add_subcommand(output, aliases=["o"])
        for mod in self.kontext.modules:
            mod.init_cli(self)

    # TODO: prepare for better Cli, without argparse
    #    self.verbosity = 0
    #    self.warn = True
    #    self.quiet = False
    #    self.params = []

    #def parse_verbosity_options(self, args=None):
    #    args = args or sys.argv
    #    skip = False
    #    for idx, arg in enumerate(args):
    #        if skip:
    #            skip = False
    #            continue
    #        elif arg == "--verbose":
    #            self.verbosity += 1
    #        elif arg.startswith("-v"):
    #            # TODO allow other letters than v
    #            self.verbosity += len(arg)-1
    #        elif arg == "--warn" or arg == "-w":
    #            self.verbosity = -1
    #        elif arg == "--quiet" or arg == "-q":
    #            self.verbosity = -2
    #        elif arg == "--warn-filter" or arg == "-W":
    #            if idx == len(args)-1:
    #                raise IndexError(f"-W/--warn-filter can not be last argument in {args}")
    #            self.parse_warning_setting(args[idx+1])
    #            skip = True
    #        else:
    #            self.params.append(arg)
    #    self.warn = self.verbosity >= -1
    #    self.quiet = self.verbosity <= -2


    def default_command(self):
        files(self)

    def custom_warn_format(self, msg, cat, filename, lineno, line):
        #if cat is UserWarning or cat is VersionWarning:
            return f'WARNING: {msg}\n'
        #return self.formatwarnings_orig(msg, cat, filename, lineno, line)

    #def get_packages(self):
    #    """a list of packages that are shown in the version command"""
    #    return ["kreate-kube"]

    def calc_dict(self):
        args = vars(self.args).get("cli_args", [])
        result = { "system": {"cli_args": args}}
        for d in self.args.define:
            k, v = d.split("=", 1)
            wrap(result).set(k, v)
        return result


    def dist_package_version(self, package_name: str):
        return importlib.metadata.version(package_name)

    def add_subcommand(self, func, name=None, aliases=[] ) -> None:
        name = name or func.__name__.replace("_","-")
        self.subcommands[name] = func
        for a in aliases:
            self.aliases[a] = name
        alias0 = aliases[0] if aliases else ""
        self.epilog += f"  {func.__name__:17} {alias0 :3} {func.__doc__ or ''} \n"

    def add_help_section(self, text: str):
        self.epilog += text + "\n"


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
        self.parser.epilog = self.epilog + "\n"
        self.args = self.parser.parse_args(self.get_argv())
        self.process_main_options(self.args)
        try:
            #self.main_konfig = self.find_main_konfig_path()

            if self.args.param:
                subcmd = self.args.param[0]
                self.subcmd = self.aliases[subcmd]
                self.params = self.args.param[1:]
            else:
                self.subcmd = "files"
                self.params = []
            self.subcommands[self.subcmd](self)
        except Exception as e:
            if self.args.verbose > 1:
                traceback.print_exc()
                self.tracer.print_all()
            elif self.args.verbose == 1:
                print(f"{type(e).__name__}: {e}")
                self.tracer.print_all()
            else:
                if isinstance(e, Warning):
                    # With a warning it might not be clear that the warning is due to a
                    print(f"stopping due to {type(e).__name__}: {e}")
                    print(f"  use -W default::{e.__class__.__name__} to override this")
                    print(f"  possibly define this as export KREATE_OPTIONS or in .env file")
                else:
                    print(f"{type(e).__name__}: {e}")
                    self.tracer.print_last()
            sys.exit(1)
        finally:
            if not self.args.keep_secrets:
                self.kontext.cleanup(", use --keep-secrets or -K option to keep it")

    def kreate_konfig(self) -> Konfig:
        path = self.find_main_konfig_path()
        dict_ = self.calc_dict()
        return Konfig(self.kontext, path, dict_=dict_, inkludes=self.args.inklude)

    #def kreate_app(self) -> App:
    #    return App(self.kreate_konfig())

    def find_main_konfig_path(self) -> Path:
        filename = self.args.konfig
        if filename is None:
            filename = os.getenv("KREATE_MAIN_KONFIG_PATH",".")
        glob_pattern = os.getenv("KREATE_MAIN_KONFIG_FILE", "kreate*.konf")
        for p in filename.split(os.pathsep):
            path = Path(p)
            if path.is_file():
                return path
            elif path.is_dir():
                logger.debug(f"checking for {glob_pattern} in dir {path}")
                possible_files = tuple(path.glob(glob_pattern))
                if len(possible_files) == 1:
                    return possible_files[0]
                elif len(possible_files) > 1:
                    raise ValueError(
                        f"Ambiguous konfig files found for {path}/{glob_pattern}: {possible_files}"
                    )
        raise ValueError(f"No main konfig file found for {filename}/{glob_pattern}")


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


    def process_main_options(self, args):
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

    def kreate_files(self) -> App:
        args = vars(self.args).get("cli_args",[])
        konfig = self.kreate_konfig()
        konfig.set_path("system.cli_args", args)
        app = App(konfig)
        app.kreate_komponents()
        app.kreate_files()
        return app

    def run_command(self, cmd_name: str, success_codes=None) -> str:
        app = self.kreate_files()
        cmd : str = app.konfig.get_path(f"system.command.{cmd_name}")
        result = self.kontext.run_shell(cmd, success_codes=success_codes)
        return result.stdout.decode()

def files(cli: Cli) -> None:
    """kreate all the files (default command)"""
    cli.kreate_files()

def output(cli: Cli) -> None:
    cli.kreate_files()
    print(cli.run_command("output"))
