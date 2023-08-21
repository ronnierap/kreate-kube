import sys
import logging
import jinja2.filters

from ..kore import KoreCli, KoreKreator,  Konfig
from ..kore._korecli import argument as argument
from . import KryptKonfig
from . import krypt_functions

logger = logging.getLogger(__name__)


class KryptKreator(KoreKreator):
    def kreate_konfig(self, filename: str = None) -> KryptKonfig:
        if not self.konfig:
            self.konfig = KryptKonfig(filename)
            self._tune_konfig(self.konfig)
        return self.konfig

    def _tune_konfig(self, konfig: Konfig):
        super()._tune_konfig(konfig)


class KryptCli(KoreCli):
    def __init__(self, kreator: KryptKreator):
        jinja2.filters.FILTERS["dekrypt"] = krypt_functions.dekrypt_str
        super().__init__(kreator)
        self.add_subcommand(dekyaml, [argument(
            "-f", "--file", help="yaml file to enkrypt")],
            aliases=["dy"])
        self.add_subcommand(dekstr, [argument(
            "-s", "--str", help="string value to dekrypt")],
            aliases=["ds"])
        self.add_subcommand(dekfile, [argument(
            "file", help=" filename to dekrypt")],
            aliases=["df"])
        self.add_subcommand(enkyaml, [argument(
            "-f", "--file", help="yaml filename to enkrypt")],
            aliases=["ey"])
        self.add_subcommand(enkfile, [argument(
            "file", help=" filename to enkrypt")],
            aliases=["ef"])
        self.add_subcommand(enkstr, [argument(
            "-s", "--str", help="string value to enkrypt")],
            aliases=["es"])


def dekyaml(cli):
    """dekrypt values in a yaml file"""
    konfig: Konfig = cli.kreator.kreate_konfig(cli.args.konfig)

    filename = (cli.args.file or
                f"{konfig.dir}/secrets-{konfig.name}-{konfig.env}.yaml")
    krypt_functions.dekrypt_yaml(filename, ".")


def dekstr(cli):
    """dekrypt string value"""
    cli.kreator.kreate_konfig(cli.args.konfig)
    value = cli.args.str
    if not value:
        if not cli.args.quiet:
            print("Enter string to dekrypt")
        value = sys.stdin.readline().strip()
    print(krypt_functions.dekrypt_str(value))


def dekfile(cli):
    "dekrypt an entire file"
    cli.kreator.kreate_konfig(cli.args.konfig)
    filename = cli.args.file
    krypt_functions.dekrypt_file(filename)


def enkyaml(cli):
    "enkrypt values in a yaml file"
    konfig: Konfig = cli.kreator.kreate_konfig(cli.args.konfig)
    filename = (cli.args.file
                or f"{konfig.dir}/secrets-{konfig.name}-{konfig.env}.yaml")
    krypt_functions.enkrypt_yaml(filename, ".")


def enkfile(cli):
    "enkrypt an entire file"
    cli.kreator.kreate_konfig(cli.args.konfig)
    filename = cli.args.file
    krypt_functions.enkrypt_file(filename)


def enkstr(cli):
    """enkrypt string value"""
    cli.kreator.kreate_konfig(cli.args.konfig)
    value = cli.args.str
    if not value:
        if not cli.args.quiet:
            print("Enter string to enkrypt")
        value = sys.stdin.readline().strip()
    print(krypt_functions.enkrypt_str(value))
