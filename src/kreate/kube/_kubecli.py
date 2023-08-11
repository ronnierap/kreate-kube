import argparse
import os
import sys
import logging
from sys import exc_info

from ..krypt import _krypt
from ..kore import KoreCli, App, AppDef
from ..kore import argument as argument
from ..kore import kreate_files as kreate_files


logger = logging.getLogger(__name__)

class KubeCli(KoreCli):
    def __init__(self):
        super().__init__()
        self.add_subcommand(build, [], aliases=["b"])
        self.add_subcommand(diff, [], aliases=["d"])
        self.add_subcommand(apply, [], aliases=["a"])
        self.add_subcommand(test, [], aliases=["t"])
        self.add_subcommand(testupdate, [], aliases=["tu"])

        self.add_subcommand(dekyaml, [argument("-f", "--file", help="yaml file to enkrypt")], aliases=["dy"])
        self.add_subcommand(dekstr, [argument("-s", "--str", help="string value to dekrypt")], aliases=["ds"])
        self.add_subcommand(dekfile, [argument("file", help=" filename to dekrypt")], aliases=["df"])
        self.add_subcommand(enkyaml, [argument("-f", "--file", help="yaml filename to enkrypt")], aliases=["ey"])
        self.add_subcommand(enkfile, [argument("file", help=" filename to enkrypt")], aliases=["ef"])
        self.add_subcommand(enkstr, [argument("-s", "--str", help="string value to enkrypt")], aliases=["es"])


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
