import logging
import os
import base64
from typing import override

from ..kore import Konfig, Module
from . import krypt_functions

logger = logging.getLogger(__name__)

def dekrypt_bytes(self, b: bytes) -> bytes:
    return krypt_functions.dekrypt_bytes(b)

def dekrypt_str(self, s: str) -> str:
    return krypt_functions.dekrypt_str(s)

class KryptKonfig(Module):
    @override
    def init_konfig(self, konfig: Konfig):
        krypt_functions._key_finder = self
        konfig.dekrypt_bytes = dekrypt_bytes
        konfig.dekrypt_str   = dekrypt_str

    def get_krypt_key(self):
        krypt_key = self.default_krypt_key().encode()
        return base64.b64encode(krypt_key).decode()

    def default_krypt_key(self):
        env_varname = self.default_krypt_key_env_var()
        logger.debug(f"getting dekrypt key from {env_varname}")
        psw = os.getenv(env_varname)
        if not psw:
            logger.warning(f"no dekrypt key given in environment var {env_varname}")
        return psw

    def default_krypt_key_env_var(self):
        varname = self.get_path("system", {}).get("krypt_key_varname", None)
        env = self.get_path("app.env")
        return varname or "KREATE_KRYPT_KEY_" + env.upper()
