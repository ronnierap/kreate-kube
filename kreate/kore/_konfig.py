import logging
from pathlib import Path
from typing import List, Sequence

from ._kontext import Kontext, get_package_version, check_requires
from ._core import deep_update, wrap
from ._repo import FileGetter
from .trace import Trace
from ._jinyaml import JinYaml

logger = logging.getLogger(__name__)


class Konfig:
    def __init__(
        self,
        kontext: Kontext,
        main_konfig_path: Path,
        dict_: dict = None,
        inkludes=None,
    ):
        self.kontext = kontext
        self.main_konfig_path = main_konfig_path
        self.tracer = self.kontext.tracer or Trace()
        logger.info(f"using main konfig from {main_konfig_path}")
        self.dekrypt_func = None
        self.dict_ = dict_ or {}
        self.yaml = wrap(self.dict_)
        self.jinyaml = JinYaml(self)
        self.file_getter = FileGetter(self, main_konfig_path.parent)
        for mod in self.kontext.modules:
            mod.init_konfig(self)
        self.already_inkluded = set()
        deep_update(
            self.dict_,
            {
                "system": {
                    "main_konfig_path": main_konfig_path,
                    "logger": logger,
                }
            },
        )
        logger.debug(self.file_getter)
        for ink in inkludes or []:
            self.inklude(ink)
        self.inklude(self.main_konfig_path.name)
        self.load_new_inkludes()
        check_requires(self.get_path("system.requires",{}), msg="system.requires: ")

    def __getitem__(self, key: str):
        return self.yaml[key]

    def get_path(self, path: str, default=None, mandatory=False):
        return self.yaml.get_path(path, default=default, mandatory=mandatory)

    def set_path(self, path: str, value):
        return self.yaml.set_path(path, value)

    def _jinja_context(self):
        result = {}
        for k in self.yaml.keys():
            v = self.yaml[k]
            result[k] = v
        return result

    def load_repo_file(self, fname: str) -> str:
        self.tracer.push(f"loading repo file: {fname}")
        result = self.file_getter.get_data(fname)
        self.tracer.pop()
        return result

    def save_repo_file(self, fname: str, data):
        self.tracer.push(f"saving repo file: {fname}")
        result = self.file_getter.save_repo_file(fname, data)
        self.tracer.pop()
        return result

    def load_new_inkludes(self):
        logger.debug("loading new inklude files")
        inkludes = self.get_path("inklude", [])
        # keep loading inkludes until all is done
        while self.load_inkludes(inkludes) > 0:
            # possible new inkludes are added
            inkludes = self.get_path("inklude", [])

    def load_inkludes(self, inkludes: List[str]) -> int:
        count = 0
        for idx, fname in enumerate(inkludes):
            fname_hash = tuple(fname)
            if fname_hash not in self.already_inkluded:
                count += 1
                self.already_inkluded.add(fname_hash)
                self.inklude(fname, idx + 1)
        logger.debug(f"inkluded {count} new files")
        return count

    def inklude_one_file(self, location: str, idx: int = None):
        # reload all repositories, in case any were added/changed
        self.tracer.push(f"inkluding {location}")
        self.file_getter.konfig_repos()
        context = self._jinja_context()
        context["my_repo_name"] = self.file_getter.get_prefix(location)
        context["args"] = {}
        if " " in location.strip():
            location, remainder = location.split(None, 1)
            for item in remainder.split():
                if "=" not in item:
                    raise ValueError(
                        "inklude params should contain = in inklude:{fname}"
                    )
                k, v = item.split("=", 1)
                context["args"][k] = v
        # new name inklude_args is more specific. args will be removed in version 2.0
        context["inklude_args"] = context["args"]
        val_yaml = self.jinyaml.render_yaml(location, context)
        if val_yaml:  # it can be empty
            deep_update(self.yaml, val_yaml, list_insert_index={"inklude": idx})
        self.tracer.pop()
        return val_yaml

    def inklude(self, location: str, idx: int = None):
        if isinstance(location, str):
            locations = [loc.strip() for loc in location.split("|")]
        elif isinstance(location, Sequence):
            locations = location
        else:
            raise TypeError(
                f"only str or list is accepted, not {type(location)}: {location}"
            )
        if len(locations) > 1:
            logger.verbose(f"trying multiple locations {locations}")
        for loc in locations:
            result = self.inklude_one_file(loc.strip(), idx=idx)
            if result:
                logger.verbose(f"inkluded  {loc}")
                break
            else:
                logger.verbose(f"ignored   {loc}")
        # self.load_new_inkludes()

    def get_kreate_version(self) -> str:
        return get_package_version("kreate-kube")

    def dekrypt_bytes(b: bytes) -> bytes:
        raise NotImplementedError("dekrypt_bytes not implemented")

    def dekrypt_str(s: str) -> str:
        raise NotImplementedError("dekrypt_str not implemented")
