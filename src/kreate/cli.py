import argparse
import os
import logging
import inspect
import collections.abc

logger = logging.getLogger(__name__)

def do_files(kreate_app, args):
    app=kreate_app(args.appdef, args.env)
    app.kreate_files()

def do_out(kreate_app, args):
    app=kreate_app(args.appdef, args.env)
    app.kreate_files()
    cmd = f"kustomize build {app.target_dir}"
    logger.info(f"running: {cmd}")
    os.system(cmd)

def do_diff(kreate_app, args):
    app=kreate_app(args.appdef, args.env)
    app.kreate_files()
    cmd = f"kustomize build {app.target_dir} | kubectl diff -f - "
    logger.info(f"running: {cmd}")
    os.system(cmd)

def do_apply(kreate_app, args):
    app=kreate_app(args.appdef, args.env)
    app.kreate_files()
    cmd = f"kustomize build {app.target_dir} | kubectl apply --dry-run -f - "
    logger.info(f"running: {cmd}")
    os.system(cmd)

def do_test(kreate_app, args):
    app=kreate_app(args.appdef, args.env)
    app.kreate_files()
    print(app.script_dir)
    cmd = f"kustomize build {app.target_dir} | diff  {app.appdef.dir}/test-{app.name}-{app.env}.out -"
    logger.info(f"running: {cmd}")
    os.system(cmd)

def do_testupdate(kreate_app, args):
    app=kreate_app(args.appdef, args.env)
    app.kreate_files()
    cmd = f"kustomize build {app.target_dir} > {app.appdef.dir}/test-{app.name}-{app.env}.out"
    logger.info(f"running: {cmd}")
    os.system(cmd)

def do_config(kreate_app, args):
    module = inspect.getmodule(kreate_app)
    func = getattr(module, "kreate_config")
    cfg = func(args.appdef, args.env)
    cfg.config().pprint() # TODO: support field="Deployment"


def run_cli(kreate_app):
    parser = argparse.ArgumentParser()
    parser.add_argument("-e","--env", action="store", default="dev")
    parser.add_argument("-a","--appdef", action="store", default="appdef.yaml")
    parser.add_argument("-v","--verbose", action="store_true")
    parser.add_argument("-w","--warn", action="store_true")
    parser.add_argument("-q","--quiet", action="store_true")


    subparsers = parser.add_subparsers(help="subcommand", description="valid subcommands", title="subcmd")
    #parser.add_subparsers(title="command", help="subcommand")
    files_cmd = subparsers.add_parser("files", help="kreate all the files (default command)", aliases=["f"])
    out_cmd = subparsers.add_parser("out", help="output all the resources", aliases=["o", "b",  "build"])
    apply_cmd = subparsers.add_parser("apply", help="apply the output to kubernetes", aliases=["a"])
    diff_cmd = subparsers.add_parser("diff", help="diff with current existing resources", aliases=["d"])
    test_cmd = subparsers.add_parser("test", help="test output against test.out file", aliases=["t"])
    testupdate_cmd = subparsers.add_parser("testupdate", help="update test.out file", aliases=["tu"])
    config_cmd = subparsers.add_parser("config", help="update test.out file", aliases=["c"])

    files_cmd.set_defaults(func=do_files)
    out_cmd.set_defaults(func=do_out)
    diff_cmd.set_defaults(func=do_diff)
    apply_cmd.set_defaults(func=do_apply)
    test_cmd.set_defaults(func=do_test)
    testupdate_cmd.set_defaults(func=do_testupdate)
    config_cmd.set_defaults(func=do_config)
    # from https://stackoverflow.com/questions/6365601/default-sub-command-or-handling-no-sub-command-with-argparse
    parser.set_defaults(func=do_files) # TODO: better way to set default command?

    args = parser.parse_args()
    env = args.env
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    elif args.warn:
        logging.basicConfig(level=logging.WARN)
    elif args.quiet:
        logging.basicConfig(level=logging.ERROR)
    else:
        logging.basicConfig(level=logging.INFO)
    args.func(kreate_app, args)
