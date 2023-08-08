import argparse
import os
import logging
from . import _jinyaml, _krypt
from ._app import App, AppDef

logger = logging.getLogger(__name__)


cli = argparse.ArgumentParser()
subparsers = cli.add_subparsers(description="valid subcommands", title="subcmd", dest="subcommand")

def argument(*name_or_flags, **kwargs):
    """Convenience function to properly format arguments to pass to the
    subcommand decorator.
    """
    return (list(name_or_flags), kwargs)

# decorator from: https://mike.depalatis.net/blog/simplifying-argparse.html
def subcommand(args=[], aliases=[], parent=subparsers):
    def decorator(func):
        parser = parent.add_parser(func.__name__, aliases=aliases, description=func.__doc__)
        for arg in args:
            parser.add_argument(*arg[0], **arg[1])
        parser.set_defaults(func=func)
    return decorator

def run_cli(kreate_appdef_func, kreate_app_func=None):
    add_main_options()
    args = cli.parse_args()
    args.kreate_appdef_func = kreate_appdef_func
    args.kreate_app_func = kreate_app_func
    process_main_options(args)
    if args.subcommand is None:
        cli.print_help()
    else:
        args.func(args)

def add_main_options():
    # from https://stackoverflow.com/questions/6365601/default-sub-command-or-handling-no-sub-command-with-argparse
    cli.set_defaults(func=files) # TODO: better way to set default command?
    cli.add_argument("-a","--appdef", action="store", default="appdef.yaml")
    cli.add_argument("-e","--env", action="store", default="dev")
    cli.add_argument("-k","--kind", action="store", default=None)
    cli.add_argument("-v","--verbose", action='count', default=0)
    cli.add_argument("-w","--warn", action="store_true")
    cli.add_argument("-q","--quiet", action="store_true")

def process_main_options(args):
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
    appdef : AppDef = args.kreate_appdef_func(args.appdef, args.env)
    app : App = args.kreate_app_func(appdef) # appdef knows the type of App to kreate
    app.kreate_files()
    return app

@subcommand([], aliases=["f"])
def files(args) -> App:
    """kreate all the files (default command)"""
    app = kreate_files(args)

@subcommand([], aliases=["b"])
def buikd(args):
    """output all the resources"""
    app = kreate_files(args)
    cmd = f"kustomize build {app.target_dir}"
    logger.info(f"running: {cmd}")
    os.system(cmd)

@subcommand([], aliases=["d"])
def diff(args):
    """diff with current existing resources"""
    app = kreate_files(args)
    cmd = f"kustomize build {app.target_dir} | kubectl diff -f - "
    logger.info(f"running: {cmd}")
    os.system(cmd)

@subcommand([], aliases=["a"])
def apply(args):
    """apply the output to kubernetes"""
    app = kreate_files(args)
    cmd = f"kustomize build {app.target_dir} | kubectl apply --dry-run -f - "
    logger.info(f"running: {cmd}")
    os.system(cmd)

@subcommand([], aliases=["t"])
def test(args):
    "test", """test output against test.out file"""
    app = kreate_files(args)
    cmd = f"kustomize build {app.target_dir} | diff  {app.appdef.dir}/test-{app.name}-{app.env}.out -"
    logger.info(f"running: {cmd}")
    os.system(cmd)

@subcommand([], aliases=["tu"])
def testupdate(args):
    "testupdate", """update test.out file"""
    app = kreate_files(args)
    cmd = f"kustomize build {app.target_dir} > {app.appdef.dir}/test-{app.name}-{app.env}.out"
    logger.info(f"running: {cmd}")
    os.system(cmd)

@subcommand([], aliases=["k"])
def konfig(args):
    "konfig", """show the konfig structure"""
    appdef : AppDef = args.kreate_appdef_func(args.appdef, args.env)
    appdef.load_konfig_files()
    appdef.konfig().pprint(field=args.kind)


@subcommand([argument("-f", "--filename", help="encrypt filename")], aliases=["dek"])
def dekrypt(args):
    """decrypt values in a yaml file"""
    appdef : AppDef = args.kreate_appdef_func(args.appdef, args.env)
    filename = args.filename or f"secrets-{appdef.name}-{appdef.env}.yaml"
    _krypt.dekrypt_yaml(filename, appdef.dir)

@subcommand([argument("-f", "--filename", help="encrypt filename")], aliases=["enk"])
def enkrypt(args):
    "encrypt values in a yaml file"
    appdef : AppDef = args.kreate_appdef_func(args.appdef, args.env)
    filename = args.filename or f"secrets-{appdef.name}-{appdef.env}.yaml"
    _krypt.enkrypt_yaml(filename, appdef.dir)
