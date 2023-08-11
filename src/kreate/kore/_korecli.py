import argparse
import logging
import traceback
from jinja2 import TemplateError
from sys import exc_info

from . import _jinyaml
from ._app import App, AppDef

logger = logging.getLogger(__name__)

def argument(*name_or_flags, **kwargs):
    """Convenience function to properly format arguments to pass to the
    subcommand decorator.
    """
    return (list(name_or_flags), kwargs)

class KoreCli:
    def __init__(self):
        self.epilog = "subcommands:\n"
        self.cli = argparse.ArgumentParser(
            prog="kreate",
            usage="kreate [optional arguments] <subcommand>",
            description="kreates files for deploying applications on kubernetes",
            #epilog="Epilog", # set later when all subcommands are known
            formatter_class=argparse.RawTextHelpFormatter
        )
        self.subparsers = self.cli.add_subparsers(
            #title="subcmd",
            #description="valid subcommands",
            dest="subcommand",
        )
        self.add_subcommand(files, [], aliases=["f"])
        self.add_subcommand(konfig, [], aliases=["k"])


    def add_subcommand(self, func, args=[], aliases=[], parent=None):
        parent = parent or self.subparsers
        self.epilog += f"  {func.__name__:10}    {aliases[0] :4} {func.__doc__ or ''} \n"
        self.parser = parent.add_parser(func.__name__, aliases=aliases, description=func.__doc__)
        for arg in args:
            self.parser.add_argument(*arg[0], **arg[1])
        self.parser.set_defaults(func=func)


    def run(self, kreate_appdef_func, kreate_app_func=None):
        self.cli.epilog = self.epilog+"\n"
        self.add_main_options()
        args = self.cli.parse_args()
        args.kreate_appdef_func = kreate_appdef_func
        args.kreate_app_func = kreate_app_func
        self.process_main_options(args)
        try:
            if args.subcommand is None:
                kreate_files(args)
            else:
                args.func(args)
        except Exception as e:
            if args.verbose:
                traceback.print_exc()
            else:
                print(f"{type(e).__name__}: {e}")
            if _jinyaml._current_jinja_file:
                lineno = jinja2_template_error_lineno()
                print(f"while processing template {_jinyaml._current_jinja_file}:{lineno}")


    def add_main_options(self):
        self.cli.add_argument("-a","--appdef", action="store", default="appdef.yaml")
        self.cli.add_argument("-k","--kind", action="store", default=None)
        self.cli.add_argument("-v","--verbose", action='count', default=0)
        self.cli.add_argument("-w","--warn", action="store_true")
        self.cli.add_argument("-q","--quiet", action="store_true")

    def process_main_options(self, args):
        if args.verbose>=2:
            logging.basicConfig(level=logging.DEBUG)
        elif args.verbose==1:
            logging.basicConfig(level=logging.DEBUG)
            _jinyaml.logger.setLevel(logging.INFO)
        elif args.warn:
            logging.basicConfig(level=logging.WARN)
        elif args.quiet:
            logging.basicConfig(level=logging.ERROR)
        else:
            logging.basicConfig(level=logging.INFO)


def kreate_files(args) -> App:
    appdef : AppDef = args.kreate_appdef_func(args.appdef)
    app : App = args.kreate_app_func(appdef)
    app.kreate_files()
    return app

def files(args) -> App:
    """kreate all the files (default command)"""
    app = kreate_files(args)

def konfig(args):
    """show the konfig structure"""
    appdef : AppDef = args.kreate_appdef_func(args.appdef)
    appdef.load_konfig_files()
    appdef.konfig().pprint(field=args.kind)


def jinja2_template_error_lineno():
    type, value, tb = exc_info()
    if not issubclass(type, TemplateError):
        return None
    if hasattr(value, 'lineno'):
        # in case of TemplateSyntaxError
        return value.lineno
    while tb:
        #print(tb.tb_frame.f_code.co_filename, tb.tb_lineno)
        if tb.tb_frame.f_code.co_filename == '<template>':
            return tb.tb_lineno
        tb = tb.tb_next
