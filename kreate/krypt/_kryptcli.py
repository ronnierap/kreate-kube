import sys
import logging
import jinja2.filters
from pathlib import Path

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
        dek_cmd = self.add_subcommand(dekrypt, aliases=["dek"])
        dek_cmd.add_argument(
            "subcmd", help="what to dekrypt", default="lines", nargs="?"
        )
        dek_cmd.add_argument("item", help="item(s) to dekrypt", default=[], nargs="*")

        enk_cmd = self.add_subcommand(enkrypt, aliases=["enk"])
        enk_cmd.add_argument(
            "subcmd", help="what to enkrypt", default="lines", nargs="?"
        )
        enk_cmd.add_argument("item", help="item(s) to enkrypt", default=[], nargs="*")

    def kreate_konfig(self, filename: str) -> KryptKonfig:
        return KryptKonfig()


def aliases():
    return {
        "f": "file",
        "s": "string",
        "str": "string",
        "l": "lines",
        "k": "lines",
    }


def dekrypt(cli: KryptCli):
    subcmd = cli.args.subcmd
    subcmd = aliases().get(subcmd, subcmd)
    if subcmd == "file":
        dekfile(cli)
    elif subcmd == "string":
        dekstr(cli)
    elif subcmd == "lines":
        dek_lines(cli)
    else:
        raise ValueError(f"unknow dekrypt subcommand {subcmd}")


def enkrypt(cli: KryptCli):
    subcmd = cli.args.subcmd
    subcmd = aliases().get(subcmd, subcmd)
    if subcmd == "file":
        enkfile(cli)
    elif subcmd == "string":
        enkstr(cli)
    elif subcmd == "lines":
        enk_lines(cli)
    else:
        raise ValueError(f"unknow dekrypt subcommand {subcmd}")


def dek_lines(cli: KryptCli):
    """dekrypt lines in a text file"""
    konfig: Konfig = cli.konfig()
    files = cli.args.item
    files = files or Path(konfig.dir).glob("secret*konf")
    for f in files:
        logger.warning(f"dekrypting: {f}")
        krypt_functions.dekrypt_lines(f, ".")


def dekstr(cli: KryptCli):
    """dekrypt string value"""
    cli.konfig()  # init konfig to set the secret value
    value = cli.args.item
    if not value:
        if not cli.args.quiet:
            print("Enter string to dekrypt")
        value = sys.stdin.readline().strip()
        print(krypt_functions.dekrypt_str(value))
    else:
        for str in value:
            print(krypt_functions.dekrypt_str(str))


def dekfile(cli: KryptCli):
    "dekrypt an entire file"
    cli.konfig()  # init konfig to set the secret value
    for f in cli.args.item:
        logger.info(f"dekrypting file {f}")
        krypt_functions.dekrypt_file(f)


def enk_lines(cli: KryptCli):
    "enkrypt lines in a text file"
    konfig: Konfig = cli.konfig()
    files = cli.args.item
    files = files or Path(konfig.dir).glob("secret*konf")
    for f in files:
        logger.warning(f"enkrypting: {f}")
        krypt_functions.enkrypt_lines(f, ".")


def enkfile(cli: KryptCli):
    "enkrypt an entire file"
    cli.konfig()
    for f in cli.args.item:
        logger.info(f"enkrypting file {f}")
        krypt_functions.enkrypt_file(f)


def enkstr(cli: KryptCli):
    """enkrypt string value"""
    cli.konfig()
    value = cli.args.item
    if not value:
        if not cli.args.quiet:
            print("Enter string to enkrypt")
        value = sys.stdin.readline().strip()
        print(krypt_functions.enkrypt_str(value))
    else:
        for str in value:
            print(krypt_functions.enkrypt_str(str))
