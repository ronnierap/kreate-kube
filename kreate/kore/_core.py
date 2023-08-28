from collections import UserDict, UserList
from collections.abc import Mapping, Sequence
import logging

logger = logging.getLogger(__name__)


def deep_update(target, other):
    for k, v in other.items():
        if isinstance(v, Mapping):
            target[k] = deep_update(target.get(k, {}), v)
        else:
            target[k] = v
    return target

class DictWrapper(UserDict):
    def __init__(self, dict):
        # do not copy the original dict as the normal UserDict does
        # but wrap the original so that updates go to the original
        # __setattr__ is used, because the data attribute does not exist yet
        super().__setattr__("data", dict)

    def __getattr__(self, attr):
        if attr not in self.data:
            raise AttributeError(f"could not find attribute {attr} in {self}")
        else:
            return wrap(self.data[attr])

    def __setattr__(self, attr, val):
        self.data[attr] = val

    def __repr__(self):
        return f"DictWrapper({self.data})"

    def _set_path(self, path: str, value):
        keys = path.split(".")
        data = self.data
        for key in keys[:-1]:
            key = key.replace("_dot_", ".")
            if key not in data:
                data[key] = {}
            data = data[key]
        final_key = keys[-1]
        final_key = final_key.replace("_dot_", ".")
        if final_key in data:
            if isinstance(data[final_key], Mapping):
                # Try to merge two Mappings
                if not isinstance(value, Mapping):
                    raise ValueError(
                        f"Can not assign non-dict {value} to"
                        f"dict {data[final_key]} for path {path}"
                    )
                data[final_key].update(value)
            else:
                data[final_key] = value
        else:
            data[final_key] = value

    def _del_path(self, path: str):
        keys = path.split(".")
        data = self.data
        for key in keys[:-1]:
            key = key.replace("_dot_", ".")
            if key not in data:
                logger.warn(f"non existent key {key} in del_path {path}")
                return
            data = data[key]
            while isinstance(data, Sequence):
                # get first and only item of list
                if len(data) == 1:
                    data = data[0]
                else:
                    logger.warn(f"list at {key} in del_path {path}")
                    return
        final_key = keys[-1]
        final_key = final_key.replace("_dot_", ".")
        if final_key in data:
            del data[final_key]
        else:
            logger.warn(f"non existent key {final_key} in del_path {path}")

    def _get_path(self, path: str, default=None):
        keys = path.split(".")
        data = self.data
        for key in keys:
            key = key.replace("_dot_", ".")
            if key not in data:
                return default
            data = data[key]
        return data


class ListWrapper(UserList):
    def __init__(self, seq) -> None:
        # do not copy the original list as the normal UserList does
        # but wrap the original so that updates go to the original
        self.data = seq

    def __getitem__(self, idx):
        # Wrap the returned value
        return wrap(self._seq[idx])


def wrap(obj):
    if isinstance(obj, Sequence) and not isinstance(obj, ListWrapper):
        return ListWrapper(obj)
    if isinstance(obj, Mapping) and not isinstance(obj, DictWrapper):
        return DictWrapper(obj)
    return obj


class DeepChain(Mapping):
    def __init__(self, *maps: Mapping):
        self._maps = maps

    def __getitem__(self, key):
        all_vals = tuple(m.get(key, None) for m in self._maps)
        vals = tuple(v for v in all_vals if v is not None)
        nrof_map_vals = sum(isinstance(v, Mapping) for v in vals)
        if nrof_map_vals > 0:
            if nrof_map_vals < len(vals):
                raise AttributeError(
                    f"key {key} is not mergeable into dictionary "
                    f"since not all values are maps {vals}"
                )
            args = list(m for m in vals)
            return DeepChain(*args)
        if len(vals) > 0:
            return vals[0]
        return None

    def __getattr__(self, attr):
        if attr not in self:
            raise AttributeError(
                f"DeepChain object could not find attribute {attr} in {self}"
            )
        else:
            return self[attr]

    def get(self, attr, default):
        if attr in self:
            return self[attr]
        return default

    def keys(self):
        result = set()
        for m in self._maps:
            for k in m.keys():
                result.add(k)
        return result

    def __len__(self):
        return len(self.keys())

    def __iter__(self):
        return iter(self.keys())

    def __contains__(self, key):
        for m in self._maps:
            if key in m:
                return True
        return False

    def __repr__(self):
        return f"DeepChain({self._maps})"

    def pprint(self, map=None, indent="", field=None):
        indent_step = "  "
        if map is None:
            map = self
        if field:
            print(f"{field}:")
            indent = indent + indent_step
            map = map.get(field, {})
        for key in sorted(map.keys()):
            val = map.get(key, None)
            if isinstance(val, Mapping):
                if len(val) == 0:
                    print(f"{indent}{key}: " + "{}")
                else:
                    print(f"{indent}{key}:")
                    self.pprint(map=val, indent=indent + indent_step)
            elif isinstance(val, str):
                print(f"{indent}{key}: {val}")
            elif isinstance(val, Sequence):
                print(f"{indent}{key}:")
                for v in val:
                    print(f"{indent}- {v}")
            else:
                print(f"{indent}{key}: {val}")
