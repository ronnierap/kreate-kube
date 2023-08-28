import inspect
import logging

from ._jinyaml import FileLocation
from ._konfig import Konfig
from ._app import App

logger = logging.getLogger(__name__)


class JinjaApp(App):
    def __init__(self, konfig: Konfig):
        super().__init__(konfig)
        self.kind_templates = {}
        self.kind_classes = {}
        self.register_std_templates()
        self.register_templates_from_konfig("templates")
        self.strukture = konfig.calc_strukture()

    def register_templates_from_konfig(self, value_key: str, cls=None):
        for key in self.konfig.yaml.get(value_key, []):
            templ = self.konfig.yaml[value_key][key]
            logger.info(f"adding custom template {key}: {templ}")
            self.register_template_file(key, filename=templ, cls=cls)

    def register_template(
        self, kind: str, cls=None, filename=None, aliases=None, package=None
    ):
        if kind in self.kind_templates:
            if cls is None:
                cls = self.kind_classes[kind]
                logger.debug(
                    f"overriding template {kind} "
                    f"using existing class {cls.__name__}"
                )
            else:
                logger.debug(f"overriding template {kind} using default class")
        filename = filename or f"{kind}.yaml"
        loc = FileLocation(
            filename=filename, package=package, dir=self.konfig.dir
        )
        logger.debug(f"registering template {kind}: {loc}")
        cls = cls or self._default_template_class()
        if cls is None:
            raise ValueError(f"No class specified for template {kind}: {loc}")
        self.kind_templates[kind] = loc
        self.kind_classes[kind] = cls
        if aliases:
            self.add_alias(kind, aliases)

    def _default_template_class(self):
        return None

    def register_template_class(
        self: str, cls, filename=None, aliases=None, package=None
    ):
        kind = cls.__name__
        self.register_template(
            kind, cls, filename=filename, aliases=aliases, package=package
        )

    def register_template_file(
        self, kind: str, cls=None, filename=None, aliases=None, package=None
    ):
        self.register_template(
            kind, cls, filename=filename, aliases=aliases, package=package
        )

    def register_std_templates(self) -> None:
        pass

    def kreate_komponent(self, kind: str, shortname: str = None):
        cls = self.kind_classes[kind]
        templ = self.kind_templates[kind]
        if inspect.isclass(cls):
            return cls(
                app=self, kind=kind, shortname=shortname, template=templ
            )
        else:
            raise ValueError(f"Unknown template type {type(cls)}, {cls}")
