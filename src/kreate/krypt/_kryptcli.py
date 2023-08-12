import sys
import logging
import jinja2.filters

from ..kore import KoreCli, AppDef
from ..kore import argument as argument
from . import _krypt

logger = logging.getLogger(__name__)


jinja2.filters.FILTERS["dekrypt"] = _krypt.dekrypt_str


class KryptCli(KoreCli):
    def __init__(self):
        super().__init__()
        self.add_subcommand(
            dekyaml, [
                argument(
                    "-f", "--file", help="yaml file to enkrypt")], aliases=["dy"])
        self.add_subcommand(
            dekstr, [
                argument(
                    "-s", "--str", help="string value to dekrypt")], aliases=["ds"])
        self.add_subcommand(
            dekfile, [
                argument(
                    "file", help=" filename to dekrypt")], aliases=["df"])
        self.add_subcommand(
            enkyaml, [
                argument(
                    "-f", "--file", help="yaml filename to enkrypt")], aliases=["ey"])
        self.add_subcommand(
            enkfile, [
                argument(
                    "file", help=" filename to enkrypt")], aliases=["ef"])
        self.add_subcommand(
            enkstr, [
                argument(
                    "-s", "--str", help="string value to enkrypt")], aliases=["es"])


def dekyaml(args):
    """dekrypt values in a yaml file"""
    appdef: AppDef = args.kreate_appdef_func(args.appdef)
    filename = args.file or f"{appdef.dir}/secrets-{appdef.name}-{appdef.env}.yaml"
    _krypt.dekrypt_yaml(filename, ".")


def dekstr(args):
    """dekrypt string value"""
    args.kreate_appdef_func(args.appdef)
    value = args.str
    if not value:
        if not args.quiet:
            print("Enter string to dekrypt")
        value = sys.stdin.readline().strip()
    print(_krypt.dekrypt_str(value))


def dekfile(args):
    "dekrypt an entire file"
    args.kreate_appdef_func(args.appdef)
    filename = args.file
    _krypt.dekrypt_file(filename)


def enkyaml(args):
    "enkrypt values in a yaml file"
    appdef: AppDef = args.kreate_appdef_func(args.appdef)
    filename = args.file or f"{appdef.dir}/secrets-{appdef.name}-{appdef.env}.yaml"
    _krypt.enkrypt_yaml(filename, ".")


def enkfile(args):
    "enkrypt an entire file"
    args.kreate_appdef_func(args.appdef)
    filename = args.file
    _krypt.enkrypt_file(filename)


def enkstr(args):
    """enkrypt string value"""
    args.kreate_appdef_func(args.appdef)
    value = args.str
    if not value:
        if not args.quiet:
            print("Enter string to enkrypt")
        value = sys.stdin.readline().strip()
    print(_krypt.enkrypt_str(value))
