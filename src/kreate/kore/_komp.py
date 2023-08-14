import logging
from collections.abc import Mapping

from ._core import DeepChain, wrap
from ._jinyaml import FileLocation, dump, load_jinyaml
from ._app import App

logger = logging.getLogger(__name__)


class Komponent:
    """An object that is parsed from a yaml template and struktureuration"""

    def __init__(self,
                 app: App,
                 shortname: str = None,
                 kind: str = None,
                 **kwargs
                 ):
        self.app = app
        self.kind = kind or self.__class__.__name__
        self.shortname = shortname or "main"
        self.strukture = self._calc_strukture(kwargs)

        self._init()
        self.skip = self.strukture.get("ignore", False)
        self.name = self.strukture.get("name", None) or self.calc_name().lower()
        if self.skip:
            # do not load the template (strukture might be missing)
            logger.info(f"ignoring {self.name}")
        else:
            logger.info(f"adding  {self.kind}.{self.shortname}")
        self.app.add(self)

    # to prevent subclass to make own constructors
    def _init(self):
        pass

    def aktivate(self):
        pass


    def __str__(self):
        return f"<Komponent {self.kind}.{self.shortname} {self.name}>"

    def calc_name(self):
        if self.shortname == "main":
            return f"{self.app.name}-{self.kind}"
        return f"{self.app.name}-{self.kind}-{self.shortname}"

    def _calc_strukture(self, extra):
        strukt = self._find_strukture()
        defaults = self._find_defaults()
        return DeepChain(extra, strukt, {"default": defaults})

    def _find_defaults(self):
        if self.kind in self.app.strukture.default:
            logger.debug(f"using defaults for {self.kind}")
            return self.app.strukture.default[self.kind]
        return {}

    def _find_strukture(self):
        typename = self.kind
        if ((typename in self.app.strukture  # ugly (( to satisfy flake8 E129))
             and self.shortname in self.app.strukture[typename])):
            logger.debug(f"using named strukture {typename}.{self.shortname}")
            return self.app.strukture[typename][self.shortname]
        logger.info(
            f"could not find strukture for {typename}.{self.shortname} in")
        return {}

    def kreate_file(self) -> None:
        filename = self.filename
        if filename:
            dir = self.dirname
            self.save_yaml(f"{dir}/{filename}")


    def invoke_options(self):
        options = self.strukture.get("options", [])
        for opt in options or []:
            if isinstance(opt, str):
                logger.debug(f"invoking {self} option {opt}")
                getattr(self, opt)()
            elif isinstance(opt, Mapping):
                for key in opt.keys():
                    val = opt.get(key)
                    if isinstance(val, Mapping):
                        logger.debug(
                            f"invoking {self} option {key}"
                            f" with kwargs parameters {val}")
                        getattr(self, key)(**dict(val))
                    elif isinstance(val, list):
                        logger.debug(
                            f"invoking {self} option {key}"
                            f" with list parameters {val}")
                        getattr(self, key)(*val)
                    elif isinstance(val, str):
                        logger.debug(
                            f"invoking {self} option {key}"
                            f" with string parameter {val}")
                        getattr(self, key)(val)
                    elif isinstance(val, int):
                        logger.debug(
                            f"invoking {self} option {key}"
                            f" with int parameter {val}")
                        getattr(self, key)(int(val))
                    else:
                        logger.warn(
                            f"option map {opt} for {self.name} not supported")

            else:
                logger.warn(f"option {opt} for {self.name} not supported")

    @property
    def dirname(self):
        return self.app.target_dir

    @property
    def filename(self):
        return f"{self.kind.lower()}-{self.shortname}.yaml"


class YamlKomponent(Komponent):
    def __init__(self,
                 app: App,
                 shortname: str = None,
                 kind: str = None,
                 template: FileLocation = None,
                 **kwargs
                 ):
        super().__init__(app, shortname, kind, **kwargs)
        template = template or self.app.kind_templates[self.kind]
        self.template = template
        #self.dir = dir

    def aktivate(self):
        self.load_yaml()
        self.invoke_options()

    def load_yaml(self):
        vars = self._template_vars()
        self.yaml = wrap(load_jinyaml(self.template, vars))

    def save_yaml(self, outfile) -> None:
        with open(outfile, 'wb') as f:
            dump(self.yaml.data, f)

    def _template_vars(self):
        return {
            "strukt": self.strukture,
            "default": self.strukture.default,
            "app": self.app,
            "my": self,
            "val": self.app.values
        }
