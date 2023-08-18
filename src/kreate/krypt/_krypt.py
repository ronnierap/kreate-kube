import logging

from ..kore import Konfig, App
from ..kore._konfig import b64encode

from . import krypt_functions

logger = logging.getLogger(__name__)


class KryptKonfig(Konfig):
    def __init__(self, filename: str = None):
        super().__init__(filename=filename)
        self.functions.update({"dekrypt": krypt_functions.dekrypt_str})
        krypt_key = self.yaml.get("krypt_key", "no-krypt-key-defined")
        krypt_functions._krypt_key = b64encode(krypt_key)


class KryptApp(App):
    pass  # Just for consistency
