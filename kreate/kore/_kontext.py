import subprocess
from typing import List, TYPE_CHECKING
from .trace import Trace

if TYPE_CHECKING:  # Only imports the below statements during type checking
    from kreate.kore._app import App
    from kreate.kore._konfig import Konfig
    from kreate.kore._cli import Cli


class Kontext:
    def __init__(self) -> None:
        self.tracer = Trace()
        self.modules : List[Module] = []
        self.packages = []

    def add_module(self, module: "Module"):
        module.init_kontext(self)
        self.modules.append(module)

    def run_shell(self, cmd: str, success_codes=None) -> subprocess.CompletedProcess:
        self.tracer.push_info(f"running command {cmd}")
        success_codes = success_codes or (0,)
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode not in success_codes:
            raise RuntimeError(f"command {cmd} resulted in return code {result.returncode}\n{result.stderr.decode()}")
        self.tracer.pop()
        return result


class Module:
    def init_kontext(self, kontext: Kontext) -> None:
        self.kontext = kontext
    def init_cli(self, cli: "Cli"): ...
    def process_cli_options(self, cli: "Cli"): ...
    def init_konfig(self, konfig: "Konfig"): ...
    def init_app(self, app: "App"): ...
    def kreate_app_komponents(self, app: "App"): ...
