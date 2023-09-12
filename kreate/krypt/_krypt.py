import logging
import os

from ..kore import Konfig, App
from ..kore._konfig import b64encode

from . import krypt_functions

logger = logging.getLogger(__name__)


class KryptKonfig(Konfig):
    def load(self):
        # before loading further konfig, set the krypt_key
        #self.functions.update({"dekrypt": krypt_functions.dekrypt_str})
        # Hack to disable testdummy when loading konfig inkludes....
        # TODO: how to censor such secrets?
        tmp = krypt_functions._dekrypt_testdummy
        krypt_functions._dekrypt_testdummy = False
        super().load()
        krypt_functions._dekrypt_testdummy = tmp
        krypt_key = self.default_krypt_key()
        krypt_functions._krypt_key = b64encode(krypt_key)

    def dekrypt_bytes(self, b: bytes) -> bytes:
        return krypt_functions.dekrypt_bytes(b)

    def default_krypt_key(self):
        env_varname = self.default_krypt_key_env_var()
        logger.debug(f"getting dekrypt key from {env_varname}")
        psw = os.getenv(env_varname)
        if not psw:
            logger.warning(
                f"no dekrypt key given in environment var {env_varname}"
            )
        return psw

    def default_krypt_key_env_var(self):
        varname = self.yaml.get("krypt_key_varname", None)
        print(varname)
        return varname or "KREATE_KRYPT_KEY_" + self.env.upper()


class KryptApp(App):
    pass  # Just for consistency
