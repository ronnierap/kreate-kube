import os
import shutil
import inspect
import logging

from ._core import DictWrapper
from ._jinyaml import load_jinyaml, FileLocation
from ._appdef import AppDef

logger = logging.getLogger(__name__)


class App():
    def __init__(self, appdef: AppDef):
        self.name = appdef.name
        self.env = appdef.env
        self.appdef = appdef
        self.values = appdef.values
        self.kind_templates = {}
        self.kind_classes = {}
        self.komponents = []
        self._kinds = {}
        self.aliases = {}
        self.register_std_templates()
        self._init()
        for key in appdef.yaml.get("templates", []):
            templ = appdef.yaml['templates'][key]
            logger.info(f"adding custom template {key}: {templ}")
            self.register_template_file(key, filename=templ)
        appdef.load_strukture_files()
        self.strukture = appdef.strukture()

    def _init(self):
        pass

    def register_template(self, kind: str, cls=None,
                          filename=None, aliases=None, package=None):
        if kind in self.kind_templates:
            if cls is None:
                cls = self.kind_classes[kind]
                logger.info(f"overriding template {kind} "
                               f"using existing class {cls.__name__}")
            else:
                logger.info(f"overriding template {kind} using "
                               f"default class")
        filename = filename or f"{kind}.yaml"
        loc = FileLocation(filename=filename,
                           package=package, dir=self.appdef.dir)
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

    def register_template_class(self: str, cls,
                                filename=None, aliases=None, package=None):
        kind = cls.__name__
        self.register_template(kind, cls, filename=filename,
                               aliases=aliases, package=package)

    def register_template_file(self, kind: str, cls=None,
                               filename=None, aliases=None, package=None):
        self.register_template(kind, cls, filename=filename,
                               aliases=aliases, package=package)

    def register_std_templates(self) -> None:
        pass

    def add_alias(self, kind: str, *aliases: str) -> None:
        if kind in self.aliases:
            self.aliases[kind].append(aliases)
        else:
            self.aliases[kind] = list(aliases)

    def get_aliases(self, kind: str):
        result = [kind, kind.lower()]
        if kind in self.aliases:
            result.append(*self.aliases[kind])
        return result

    def add(self, res) -> None:
        if not res.skip:
            self.komponents.append(res)
        map = self._kinds.get(res.kind, None)
        if map is None:
            map = DictWrapper({})
            self.get_aliases(res.kind)
            for alias in self.get_aliases(res.kind):
                self._kinds[alias] = map

        map[res.shortname] = res

    def __getattr__(self, attr):
        if attr in self.__dict__ or attr == "_dict":
            return super().__getattribute__(attr)
        return self._kinds.get(attr, None)

    def kreate_komponent(self, kind: str, shortname: str = None, **kwargs):
        cls = self.kind_classes[kind]
        templ = self.kind_templates[kind]
        if inspect.isclass(cls):
            return cls(app=self, kind=kind,
                       shortname=shortname, template=templ, **kwargs)
        else:
            raise ValueError(f"Unknown template type {type(cls)}, {cls}")

    def aktivate(self):
        for komp in self.komponents:
            logger.debug(
                f"aktivating {self.kind}.{self.shortname} at {self.template}")
            komp.aktivate()

    def kreate_files(self):
        if os.path.exists(self.target_dir) and os.path.isdir(self.target_dir):
            shutil.rmtree(self.target_dir)
        os.makedirs(self.target_dir, exist_ok=True)

        for komp in self.komponents:
            if (komp.filename):
                logger.info(f"kreating file {komp.filename}")
                komp.kreate_file()
            else:
                logger.info(f"skipping file for {komp.kind}.{komp.shortname}")

    def _shortnames(self, kind: str) -> list:
        if kind in self.strukture:
            return self.strukture[kind].keys()
        return []

    def kreate_komponents_from_strukture(self):
        for kind in sorted(self.strukture.keys()):
            if kind in self.kind_classes:
                for shortname in sorted(self.strukture[kind].keys()):
                    logger.info(f"kreating komponent {kind}.{shortname}")
                    self.kreate_komponent(kind, shortname)
            elif kind != "default":
                logger.warning(f"Unknown toplevel komponent {kind}")
