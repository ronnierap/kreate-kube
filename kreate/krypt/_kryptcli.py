import sys
import logging
import jinja2.filters

from ..kore import KoreCli, Konfig
from ..kore._korecli import argument as argument
from . import KryptKonfig
from . import krypt_functions

logger = logging.getLogger(__name__)


class KryptCli(KoreCli):
    def __init__(self):
        jinja2.filters.FILTERS["dekrypt"] = krypt_functions.dekrypt_str
        super().__init__()
        self.add_krypt_options()
        self.add_krypt_subcommands()

    def add_krypt_options(self):
        self.cli.add_argument(
            "--testdummy", action="store_true", help="do not dekrypt values"
        )

    def process_main_options(self, args):
        super().process_main_options(args)
        if args.testdummy:
            krypt_functions._dekrypt_testdummy = True

    def add_krypt_subcommands(self):
        self.add_subcommand(
            dekyaml,
            [argument("-f", "--file", help="yaml file to enkrypt")],
            aliases=["dy"],
        )
        self.add_subcommand(
            dekstr,
            [argument("-s", "--str", help="string value to dekrypt")],
            aliases=["ds"],
        )
        self.add_subcommand(
            dekfile,
            [argument("file", help=" filename to dekrypt")],
            aliases=["df"],
        )
        self.add_subcommand(
            enkyaml,
            [argument("-f", "--file", help="yaml filename to enkrypt")],
            aliases=["ey"],
        )
        self.add_subcommand(
            enkfile,
            [argument("file", help=" filename to enkrypt")],
            aliases=["ef"],
        )
        self.add_subcommand(
            enkstr,
            [argument("-s", "--str", help="string value to enkrypt")],
            aliases=["es"],
        )

    def _kreate_konfig(self, filename: str) -> KryptKonfig:
        return KryptKonfig()


def dekyaml(cli: KryptCli):
    """dekrypt values in a yaml file"""
    konfig: Konfig = cli.konfig()

    filename = (
        cli.args.file
        or f"{konfig.dir}/secrets-{konfig.appname}-{konfig.env}.yaml"
    )
    krypt_functions.dekrypt_yaml(filename, ".")


def dekstr(cli: KryptCli):
    """dekrypt string value"""
    cli.konfig()  # init konfig to set the secret value
    value = cli.args.str
    if not value:
        if not cli.args.quiet:
            print("Enter string to dekrypt")
        value = sys.stdin.readline().strip()
    print(krypt_functions.dekrypt_str(value))


def dekfile(cli: KryptCli):
    "dekrypt an entire file"
    cli.konfig()  # init konfig to set the secret value
    filename = cli.args.file
    krypt_functions.dekrypt_file(filename)


def enkyaml(cli: KryptCli):
    "enkrypt values in a yaml file"
    konfig: Konfig = cli.konfig()
    filename = (
        cli.args.file
        or f"{konfig.dir}/secrets-{konfig.appname}-{konfig.env}.yaml"
    )
    krypt_functions.enkrypt_yaml(filename, ".")


def enkfile(cli: KryptCli):
    "enkrypt an entire file"
    cli.konfig()
    filename = cli.args.file
    krypt_functions.enkrypt_file(filename)


def enkstr(cli: KryptCli):
    """enkrypt string value"""
    cli.konfig()
    value = cli.args.str
    if not value:
        if not cli.args.quiet:
            print("Enter string to enkrypt")
        value = sys.stdin.readline().strip()
    print(krypt_functions.enkrypt_str(value))
