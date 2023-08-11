import logging
from collections.abc import Mapping

from ._core import  DeepChain
from ._jinyaml import YamlBase
from ._app import App
from ._jinyaml import FileLocation

logger = logging.getLogger(__name__)


class Komponent(YamlBase):
    """An object that is parsed from a yaml template and konfiguration"""
    def __init__(self, app: App,
                 kind: str = None,
                 shortname: str = None,
                 template: FileLocation = None,
                 **kwargs
                 ):
        self.app = app
        self.kind = kind or self.__class__.__name__
        self.shortname = shortname or "main"
        self.konfig = self._calc_konfig(kwargs)
        template = template or self.app.kind_templates[self.kind]

        YamlBase.__init__(self, template)
        self._init()
        self.skip = self.konfig.get("ignore", False)
        self.name = self.konfig.get("name", None) or self.calc_name().lower()
        if self.skip:
            # do not load the template (konfig might be missing)
            logger.info(f"ignoring {self.name}")
        else:
            logger.debug(f"parsing {self.kind}.{self.shortname} at {self.template}")
            self.load_yaml()
        self.app.add(self)
        self.invoke_options()

    # to prevent subclass to make own constructors
    def _init(self):
        pass

    def __str__(self):
        return f"<Komponent {self.kind}.{self.shortname} {self.name}>"

    def calc_name(self):
        if self.shortname == "main":
            return f"{self.app.name}-{self.kind}"
        return f"{self.app.name}-{self.kind}-{self.shortname}"

    def _calc_konfig(self, extra):
        konf = self._find_konfig()
        defaults = self._find_defaults()
        return DeepChain(extra, konf, {"default": defaults})

    def _find_defaults(self):
        if self.kind in self.app.konfig.default:
            logger.debug(f"using defaults for {self.kind}")
            return self.app.konfig.default[self.kind]
        return {}

    def _find_konfig(self):
        typename = self.kind
        if typename in self.app.konfig and self.shortname in self.app.konfig[typename]:
            logger.debug(f"using named konfig {typename}.{self.shortname}")
            return  self.app.konfig[typename][self.shortname]
        logger.info(f"could not find konfig for {typename}.{self.shortname} in")
        return {}

    def kreate_file(self) -> None:
        filename = self.filename
        if filename:
            dir = self.dirname
            self.save_yaml(f"{dir}/{filename}")

    def _template_vars(self):
        return {
            "konf": self.konfig,
            "default": self.konfig.default,
            "app": self.app,
            "my": self,
            "val": self.app.values
        }

    def invoke_options(self):
        options = self.konfig.get("options", [])
        for opt in options or []:
            if type(opt) == str:
                logger.debug(f"invoking {self} option {opt}")
                getattr(self, opt)()
            elif isinstance(opt, Mapping):
                for key in opt.keys():
                    val = opt.get(key)
                    if isinstance(val, Mapping):
                        logger.debug(f"invoking {self} option {key} with kwargs parameters {val}")
                        getattr(self, key)(**dict(val))
                    elif isinstance(val, list):
                        logger.debug(f"invoking {self} option {key} with list parameters {val}")
                        getattr(self, key)(*val)
                    elif isinstance(val, str):
                        logger.debug(f"invoking {self} option {key} with string parameter {val}")
                        getattr(self, key)(val)
                    elif isinstance(val, int):
                        logger.debug(f"invoking {self} option {key} with int parameter {val}")
                        getattr(self, key)(int(val))
                    else:
                        logger.warn(f"option map {opt} for {self.name} not supported")

            else:
                logger.warn(f"option {opt} for {self.name} not supported")


    @property
    def dirname(self):
        return self.app.target_dir

    @property
    def filename(self):
        return f"{self.kind.lower()}-{self.shortname}.yaml"
