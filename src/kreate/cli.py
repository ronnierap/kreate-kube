import argparse
import os
import logging
from . import jinyaml

logger = logging.getLogger(__name__)

class Cli():
    def __init__(self, kreate_appdef_func):
        self.kreate_appdef_func = kreate_appdef_func
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("-e","--env", action="store", default="dev")
        self.parser.add_argument("-a","--appdef", action="store", default="appdef.yaml")
        self.parser.add_argument("-k","--kind", action="store", default=None)
        self.parser.add_argument("-v","--verbose", action='count', default=0)
        self.parser.add_argument("-w","--warn", action="store_true")
        self.parser.add_argument("-q","--quiet", action="store_true")


        subparsers = self.parser.add_subparsers(help="subcommand", description="valid subcommands", title="subcmd")
        #parser.add_subparsers(title="command", help="subcommand")
        self.files_cmd = subparsers.add_parser("files", help="kreate all the files (default command)", aliases=["f"])
        self.out_cmd = subparsers.add_parser("out", help="output all the resources", aliases=["o", "b",  "build"])
        self.apply_cmd = subparsers.add_parser("apply", help="apply the output to kubernetes", aliases=["a"])
        self.diff_cmd = subparsers.add_parser("diff", help="diff with current existing resources", aliases=["d"])
        self.test_cmd = subparsers.add_parser("test", help="test output against test.out file", aliases=["t"])
        self.testupdate_cmd = subparsers.add_parser("testupdate", help="update test.out file", aliases=["tu"])
        self.konfig_cmd = subparsers.add_parser("konfig", help="show the konfig structure", aliases=["k"])

        self.files_cmd.set_defaults(func=_do_files)
        self.out_cmd.set_defaults(func=_do_out)
        self.diff_cmd.set_defaults(func=_do_diff)
        self.apply_cmd.set_defaults(func=_do_apply)
        self.test_cmd.set_defaults(func=_do_test)
        self.testupdate_cmd.set_defaults(func=_do_testupdate)
        self.konfig_cmd.set_defaults(func=_do_konfig)
        # from https://stackoverflow.com/questions/6365601/default-sub-command-or-handling-no-sub-command-with-argparse
        self.parser.set_defaults(func=_do_files) # TODO: better way to set default command?

    def run(self):
        args = self.parser.parse_args()
        env = args.env
        if args.verbose>=2:
            logging.basicConfig(level=logging.DEBUG)
        elif args.verbose==1:
            logging.basicConfig(level=logging.DEBUG)
            jinyaml.logger.setLevel(logging.INFO)
        elif args.warn:
            logging.basicConfig(level=logging.WARN)
        elif args.quiet:
            logging.basicConfig(level=logging.ERROR)
        else:
            logging.basicConfig(level=logging.INFO)
        args.func(self.kreate_appdef_func, args)


def _do_files(kreate_appdef_func, args):
    appdef = kreate_appdef_func(args.appdef, args.env)
    app = appdef.kreate_app()
    app.kreate_files()
    return app

def _do_out(kreate_appdef_func, args):
    app = _do_files(kreate_appdef_func, args)
    cmd = f"kustomize build {app.target_dir}"
    logger.info(f"running: {cmd}")
    os.system(cmd)

def _do_diff(kreate_appdef_func, args):
    app = _do_files(kreate_appdef_func, args)
    cmd = f"kustomize build {app.target_dir} | kubectl diff -f - "
    logger.info(f"running: {cmd}")
    os.system(cmd)

def _do_apply(kreate_appdef_func, args):
    app = _do_files(kreate_appdef_func, args)
    cmd = f"kustomize build {app.target_dir} | kubectl apply --dry-run -f - "
    logger.info(f"running: {cmd}")
    os.system(cmd)

def _do_test(kreate_appdef_func, args):
    app = _do_files(kreate_appdef_func, args)
    cmd = f"kustomize build {app.target_dir} | diff  {app.appdef.dir}/test-{app.name}-{app.env}.out -"
    logger.info(f"running: {cmd}")
    os.system(cmd)

def _do_testupdate(kreate_appdef_func, args):
    app = _do_files(kreate_appdef_func, args)
    cmd = f"kustomize build {app.target_dir} > {app.appdef.dir}/test-{app.name}-{app.env}.out"
    logger.info(f"running: {cmd}")
    os.system(cmd)

def _do_konfig(kreate_appdef_func, args):
    cfg = kreate_appdef_func(args.appdef, args.env)
    cfg.konfig().pprint(field=args.kind)
