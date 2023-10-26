import logging
from ..kore import JinjaApp, Konfig
from ..krypt import KryptKonfig

logger = logging.getLogger(__name__)


class KubeApp(JinjaApp):
    def __init__(self, konfig: Konfig):
        super().__init__(konfig)
        self.namespace = konfig.get_path("app.namespace", f"{self.appname}-{self.env}")


class KubeKonfig(KryptKonfig):
    pass
