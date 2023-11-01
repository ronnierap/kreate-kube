import logging
import os
import base64

from ..kore import Konfig, App
from . import krypt_functions

logger = logging.getLogger(__name__)


class KryptKonfig(Konfig):
    def __init__(self, filename: str = None, dict_: dict = None, inkludes=None):
        krypt_functions._konfig = self
        super().__init__(location=filename, dict_=dict_, inkludes=inkludes)

    def dekrypt_bytes(self, b: bytes) -> bytes:
        return krypt_functions.dekrypt_bytes(b)

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


class KryptApp(App):
    pass  # Just for consistency
