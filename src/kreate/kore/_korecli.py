import argparse
import logging
import traceback
from jinja2 import TemplateError, filters
from sys import exc_info

from . import _jinyaml
from ._app import App, AppDef
from ._appdef import b64encode
import importlib.metadata

logger = logging.getLogger(__name__)


class KoreKreator:
    def __init__(self, kreate_app_func=None) -> None:
        self.kreate_app_func = kreate_app_func

    def kreate_cli(self):
        return KoreCli(self)

    def kreate_appdef(self, filename):
        filters.FILTERS["b64encode"] = b64encode
        appdef = AppDef(filename)
        self.tune_appdef(appdef)
        return appdef

    def _app_class(self):
        raise NotImplementedError()

    def kreate_app(self, appdef: AppDef) -> App:
        if self.kreate_app_func:
            return self.kreate_app_func(appdef)
        app = self._app_class()(appdef)
        app.kreate_komponents_from_strukture()
        app.aktivate()
        return app


def argument(*name_or_flags, **kwargs):
    """Convenience function to properly format arguments to pass to the
    subcommand decorator.
    """
    return (list(name_or_flags), kwargs)


class KoreCli:
    def __init__(self, kreator: KoreKreator):
        self.kreator = kreator
        self.epilog = "subcommands:\n"
        self.cli = argparse.ArgumentParser(
            prog="kreate",
            usage="kreate [optional arguments] <subcommand>",
            description=(
                "kreates files for deploying applications on kubernetes"),
            formatter_class=argparse.RawTextHelpFormatter
        )
        self.subparsers = self.cli.add_subparsers(
            # title="subcmd",
            # description="valid subcommands",
            dest="subcommand",
        )
        self.add_subcommand(files, [], aliases=["f"])
        self.add_subcommand(view_strukture, [], aliases=["vs"])
        self.add_subcommand(view_version, [], aliases=["version"])

    def dist_package_version(self, package_name: str):
        return importlib.metadata.version(package_name)

    def add_subcommand(self, func, args=[], aliases=[], parent=None):
        parent = parent or self.subparsers
        alias0 = aliases[0] if aliases else ""
        self.epilog += (f"  {func.__name__:10}    {alias0 :4}"
                        f" {func.__doc__ or ''} \n")
        self.parser = parent.add_parser(
            func.__name__, aliases=aliases, description=func.__doc__)
        for arg in args:
            self.parser.add_argument(*arg[0], **arg[1])
        self.parser.set_defaults(func=func)

    def run(self, ):
        self.cli.epilog = self.epilog+"\n"
        self.add_main_options()
        self.args = self.cli.parse_args()
        self.process_main_options(self.args)
        try:
            if self.args.subcommand is None:
                kreate_files(self)
            else:
                self.args.func(self)
        except Exception as e:
            if self.args.verbose:
                traceback.print_exc()
            else:
                print(f"{type(e).__name__}: {e}")
            if _jinyaml._current_jinja_file:
                lineno = jinja2_template_error_lineno()
                print(f"while processing template "
                      f"{_jinyaml._current_jinja_file}:{lineno}")

    def add_main_options(self):
        self.cli.add_argument(
            "-a", "--appdef", action="store", default="appdef.yaml")
        self.cli.add_argument("-k", "--kind", action="store", default=None)
        self.cli.add_argument("-v", "--verbose", action='count', default=0)
        self.cli.add_argument("-w", "--warn", action="store_true")
        self.cli.add_argument("-q", "--quiet", action="store_true")

    def process_main_options(self, args):
        if args.verbose >= 2:
            logging.basicConfig(level=logging.DEBUG)
        elif args.verbose == 1:
            logging.basicConfig(level=logging.DEBUG)
            _jinyaml.logger.setLevel(logging.INFO)
        elif args.warn:
            logging.basicConfig(level=logging.WARN)
        elif args.quiet:
            logging.basicConfig(level=logging.ERROR)
        else:
            logging.basicConfig(level=logging.INFO)


def kreate_files(cli: KoreCli) -> App:
    appdef: AppDef = cli.kreator.kreate_appdef(cli.args.appdef)
    app: App = cli.kreator.kreate_app(appdef)
    app.kreate_files()
    return app


def files(cli: KoreCli) -> App:
    """kreate all the files (default command)"""
    kreate_files(cli)


def view_strukture(cli: KoreCli):
    """show the application strukture"""
    appdef: AppDef = cli.kreator.kreate_appdef(cli.args.appdef)
    appdef.calc_strukture().pprint(field=cli.args.kind)


def view_version(cli: KoreCli):
    """show the version"""
    version = cli.dist_package_version("kreate-kube")
    print(f"kreate-kube: {version}")


def jinja2_template_error_lineno():
    type, value, tb = exc_info()
    if not issubclass(type, TemplateError):
        return None
    if hasattr(value, 'lineno'):
        # in case of TemplateSyntaxError
        return value.lineno
    while tb:
        # print(tb.tb_frame.f_code.co_filename, tb.tb_lineno)
        if tb.tb_frame.f_code.co_filename == '<template>':
            return tb.tb_lineno
        tb = tb.tb_next
