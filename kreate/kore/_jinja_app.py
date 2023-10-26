import inspect
import logging

from ._konfig import Konfig
from ._app import App

logger = logging.getLogger(__name__)


def load_class(name):
    components = name.split(".")
    mod = __import__(components[0])
    for comp in components[1:-1]:
        mod = getattr(mod, comp)
    return getattr(mod, components[-1])


class JinjaApp(App):
    def __init__(self, konfig: Konfig):
        super().__init__(konfig)
        self.kind_templates = {}
        self.kind_classes = {}
        self.register_std_templates()
        self.register_templates_from_konfig()

    def register_templates_from_konfig(self):
        templates = self.konfig.get_path("system.template", {})
        for key, _def in templates.items():
            logger.debug(f"adding custom template {key}")
            if _def.get("template"):
                if _def.get("class"):
                    self.register_template_path(key, _def["class"], _def["template"])
                else:
                    self.kind_templates = _def["template"]

    def register_template_path(self, kind: str, clsname: str, path: str) -> None:
        self.kind_templates[kind] = path
        self.kind_classes[kind] = load_class(clsname)

    def register_template(self, kind: str, cls, filename=None, package=None):
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
        if package:
            filename = f"py:{package.__name__}:{filename}"
        logger.debug(f"registering template {kind}: {filename}")
        if cls is None:
            raise ValueError(f"No class specified for template {kind}: {filename}")
        self.kind_templates[kind] = filename
        self.kind_classes[kind] = cls

    def register_template_class(self: str, cls, filename=None, package=None):
        kind = cls.__name__
        self.register_template(kind, cls, filename=filename, package=package)

    def register_template_file(self, kind: str, cls=None, filename=None, package=None):
        self.register_template(kind, cls, filename=filename, package=package)

    def register_std_templates(self) -> None:
        pass

    def kreate_komponent(self, kind: str, shortname: str = None):
        cls = self.kind_classes[kind]
        templ = self.kind_templates[kind]
        if inspect.isclass(cls):
            return cls(app=self, kind=kind, shortname=shortname)
        else:
            raise ValueError(f"Unknown template type {type(cls)}, {cls}")
