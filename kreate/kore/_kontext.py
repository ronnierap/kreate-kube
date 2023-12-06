import subprocess
import sys
import logging
import warnings
import importlib.metadata

from pathlib import Path
from typing import Mapping, List, Set, TYPE_CHECKING, Sequence
from packaging.specifiers import SpecifierSet
from packaging.version import Version

from . import dotenv
from .trace import Trace

if TYPE_CHECKING:  # Only imports the below statements during type checking
    from kreate.kore._app import App
    from kreate.kore._konfig import Konfig
    from kreate.kore._cli import Cli

logging.VERBOSE = 15
logging.addLevelName(logging.VERBOSE, "VERBOSE")
logging.Logger.verbose = lambda inst, msg, *args, **kwargs: inst.log(
    logging.VERBOSE, msg, *args, **kwargs
)
logging.verbose = lambda msg, *args, **kwargs: logging.log(
    logging.VERBOSE, msg, *args, **kwargs
)
logger = logging.getLogger(__name__)


def load_class(name):
    components = name.split(".")
    mod = __import__(components[0])
    for comp in components[1:-1]:
        mod = getattr(mod, comp)
    return getattr(mod, components[-1])


class VersionWarning(RuntimeWarning):
    pass


class Kontext:
    def __init__(self) -> None:
        self.tracer = Trace()
        self.modules: List[Module] = []
        self.packages = []
        self.cleanup_paths: Set[Path] = set()
        self.load_dotenv()

    def add_module(self, module: "Module"):
        module.init_kontext(self)
        self.modules.append(module)

    def run_shell(self, cmd: str, success_codes=None) -> subprocess.CompletedProcess:
        self.tracer.push_info(f"running command {cmd}")
        success_codes = success_codes or (0,)
        result = subprocess.run(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if result.returncode not in success_codes:
            raise RuntimeError(
                f"command {cmd} resulted in return code {result.returncode}\n{result.stderr.decode()}"
            )
        self.tracer.pop()
        return result

    def add_cleanup_path(self, path: Path):
        self.cleanup_paths.add(Path(path))

    def cleanup(self, msg: str):
        for path in self.cleanup_paths:
            if path.exists():
                logger.info(f"removing {path}{msg}")
                if path.is_dir():
                    path.rmdir()
                else:
                    path.unlink()

    def load_dotenv(self) -> None:
        # Primitive way to check if to load ENV vars before parsing vars
        # .env needs to be loaded before arg parsing, since it may
        # contain KREATE_OPTIONS
        load_dot_env = True
        load_kreate_env = True
        for arg in sys.argv:
            if arg == "--no-dotenv":
                load_dot_env = False
            if arg == "--no-kreate-env":
                load_kreate_env = False
        try:
            if load_dot_env:
                dotenv.load_env(Path.cwd() / ".env")
            if load_kreate_env:
                dotenv.load_env(Path.home() / ".config/kreate/kreate.env")
        except Exception as e:
            logger.error(
                f"ERROR loading .env file, " f"remove .env file or specify --no-dotenv"
            )
            raise


class Module:
    def init_kontext(self, kontext: Kontext) -> None:
        self.kontext = kontext

    def init_cli(self, cli: "Cli"):
        ...

    def process_cli_options(self, cli: "Cli"):
        ...

    def init_konfig(self, konfig: "Konfig"):
        ...

    def init_app(self, app: "App"):
        ...

    def kreate_app_komponents(self, app: "App"):
        ...


def get_package_version(package: str) -> str:
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return "Unknown"

def check_requires(specifiers: Mapping, force: bool = False, msg: str = ""):
    dev_versions = ["Unknown"]  #  , "rc", "editable"]
    for package, specifier in specifiers.items():
        version = get_package_version(package)
        if any(txt in version for txt in dev_versions) and not force:
            logger.debug(f"skipping check for development version {version}")
            break
        if isinstance(specifier, Sequence) and not isinstance(specifier, str):
            specifier = ",".join(specifier)
        if not SpecifierSet(specifier).contains(Version(version)):
            warnings.warn(
                f"{msg}Invalid {package} version {version} for specifier {specifier}",
                VersionWarning,
        )
