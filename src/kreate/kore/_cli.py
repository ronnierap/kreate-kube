import argparse
import os
import sys
import logging
from . import _jinyaml
from ..krypt import _krypt
from ._app import App, AppDef
import traceback
from jinja2 import TemplateError
from sys import exc_info

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
        self.add_subcommand(build, [], aliases=["b"])
        self.add_subcommand(diff, [], aliases=["d"])
        self.add_subcommand(apply, [], aliases=["a"])
        self.add_subcommand(test, [], aliases=["t"])
        self.add_subcommand(testupdate, [], aliases=["tu"])
        self.add_subcommand(konfig, [], aliases=["k"])
        self.add_subcommand(dekyaml, [argument("-f", "--file", help="yaml file to enkrypt")], aliases=["dy"])
        self.add_subcommand(dekstr, [argument("-s", "--str", help="string value to dekrypt")], aliases=["ds"])
        self.add_subcommand(dekfile, [argument("file", help=" filename to dekrypt")], aliases=["df"])
        self.add_subcommand(enkyaml, [argument("-f", "--file", help="yaml filename to enkrypt")], aliases=["ey"])
        self.add_subcommand(enkfile, [argument("file", help=" filename to enkrypt")], aliases=["ef"])
        self.add_subcommand(enkstr, [argument("-s", "--str", help="string value to enkrypt")], aliases=["es"])



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
    app : App = args.kreate_app_func(appdef) # appdef knows the type of App to kreate
    app.kreate_files()
    return app

def files(args) -> App:
    """kreate all the files (default command)"""
    app = kreate_files(args)

def build(args):
    """output all the resources"""
    app = kreate_files(args)
    cmd = f"kustomize build {app.target_dir}"
    logger.info(f"running: {cmd}")
    os.system(cmd)

def diff(args):
    """diff with current existing resources"""
    app = kreate_files(args)
    cmd = f"kustomize build {app.target_dir} | kubectl --context={app.env} -n {app.namespace} diff -f - "
    logger.info(f"running: {cmd}")
    os.system(cmd)

def apply(args):
    """apply the output to kubernetes"""
    app = kreate_files(args)
    cmd = f"kustomize build {app.target_dir} | kubectl apply --dry-run -f - "
    logger.info(f"running: {cmd}")
    os.system(cmd)

def test(args):
    """test output against test.out file"""
    _krypt._dekrypt_testdummy = True  # Do not dekrypt secrets for testing
    app = kreate_files(args)
    cmd = f"kustomize build {app.target_dir} | diff  {app.appdef.dir}/expected-output-{app.name}-{app.env}.out -"
    logger.info(f"running: {cmd}")
    os.system(cmd)

def testupdate(args):
    """update test.out file"""
    _krypt._dekrypt_testdummy = True  # Do not dekrypt secrets for testing
    app = kreate_files(args)
    cmd = f"kustomize build {app.target_dir} > {app.appdef.dir}/expected-output-{app.name}-{app.env}.out"
    logger.info(f"running: {cmd}")
    os.system(cmd)

def konfig(args):
    """show the konfig structure"""
    appdef : AppDef = args.kreate_appdef_func(args.appdef)
    appdef.load_konfig_files()
    appdef.konfig().pprint(field=args.kind)


def dekyaml(args):
    """dekrypt values in a yaml file"""
    appdef : AppDef = args.kreate_appdef_func(args.appdef)
    filename = args.file or f"{appdef.dir}/secrets-{appdef.name}-{appdef.env}.yaml"
    _krypt.dekrypt_yaml(filename, ".")

def dekstr(args):
    """dekrypt string value"""
    appdef : AppDef = args.kreate_appdef_func(args.appdef)
    value = args.str
    if not value:
        if not args.quiet: print("Enter string to dekrypt")
        value = sys.stdin.readline().strip()
    print(_krypt.dekrypt_str(value))

def dekfile(args):
    "dekrypt an entire file"
    appdef : AppDef = args.kreate_appdef_func(args.appdef)
    filename = args.file
    _krypt.dekrypt_file(filename)

def enkyaml(args):
    "enkrypt values in a yaml file"
    appdef : AppDef = args.kreate_appdef_func(args.appdef)
    filename = args.file or f"{appdef.dir}/secrets-{appdef.name}-{appdef.env}.yaml"
    _krypt.enkrypt_yaml(filename, ".")

def enkfile(args):
    "enkrypt an entire file"
    appdef : AppDef = args.kreate_appdef_func(args.appdef)
    filename = args.file
    _krypt.enkrypt_file(filename)

def enkstr(args):
    """enkrypt string value"""
    appdef : AppDef = args.kreate_appdef_func(args.appdef)
    value = args.str
    if not value:
        if not args.quiet: print("Enter string to enkrypt")
        value = sys.stdin.readline().strip()
    print(_krypt.enkrypt_str(value))


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
