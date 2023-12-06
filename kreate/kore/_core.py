import io
import logging
import re
import sys
from collections import UserDict, UserList
from collections.abc import Mapping, Sequence

logger = logging.getLogger(__name__)


def deep_update(
    target: Mapping,
    other: Mapping,
    overwrite=True,
    list_insert_index: dict = None,
) -> None:
    if other.get("_do_not_overwrite", False):
        overwrite = False
    for k, v in other.items():
        if isinstance(v, Mapping):
            if k not in target:
                target[k] = dict(v)  # use a copy
            elif isinstance(target[k], Mapping):
                deep_update(target[k], v, overwrite=overwrite)
            else:
                raise ValueError(
                    f"trying to merge key {k} map {v} into non-map {target[k]}"
                )
        elif isinstance(v, Sequence) and not isinstance(v, str):
            if k not in target:
                target[k] = list(v)  # use a copy
            elif isinstance(target[k], Sequence) and not isinstance(target[k], str):
                if list_insert_index and k in list_insert_index:
                    idx = list_insert_index[k]
                    target[k][idx:idx] = v
                else:
                    for item in v:
                        target[k].append(item)
            else:
                raise ValueError(
                    f"trying to merge key {k} sequence {v}"
                    f" into non-sequence {target[k]}"
                )
        else:
            if overwrite or k not in target:
                # this key is special, should find better way
                if k != "_do_not_overwrite":
                    target[k] = v


class DictWrapper(UserDict):
    def __init__(self, dict):
        # do not copy the original dict as the normal UserDict does
        # but wrap the original so that updates go to the original
        self.data = dict

    def __getattr__(self, attr):
        if attr not in self.data:
            raise AttributeError(
                f"could not find attribute {attr} in {self}, {self.data}"
            )
        else:
            return wrap(self.data[attr])

    def __repr__(self):
        return f"DictWrapper({self.data})"

    def pprint_str(self, indent=""):
        output = io.StringIO()
        pprint_map(self, indent=indent, file=output)
        result = output.getvalue()
        output.close
        return result

    def deep_update_path(self, path: str, value):
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
                deep_update(data[final_key], value)
            else:
                data[final_key] = value
        elif final_key == "[0]" and isinstance(data, Sequence):
            deep_update(data[0], value)
        else:
            data[final_key] = value

    # TODO: Will be removed in 2.0
    def _set_path(self, path: str, value):
        self.set_path(path, value)

    def set_path(self, path: str, value):
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
        elif final_key == "[0]" and isinstance(data, Sequence):
            deep_update(data[0], value)
        else:
            data[final_key] = value

    # TODO: Will be removed in 2.0
    def _del_path(self, path: str):
        self.del_path(path)

    def del_path(self, path: str):
        keys = path.split(".")
        data = self.data
        for key in keys[:-1]:
            key = key.replace("_dot_", ".")
            if key not in data:
                logger.warning(f"non existent key {key} in del_path {path}")
                return
            data = data[key]
            while isinstance(data, Sequence):
                # get first and only item of list
                if len(data) == 1:
                    data = data[0]
                else:
                    logger.warning(f"list at {key} in del_path {path}")
                    return
        final_key = keys[-1]
        final_key = final_key.replace("_dot_", ".")
        if final_key in data:
            del data[final_key]
        else:
            logger.warning(f"non existent key {final_key} in del_path {path}")

    def get(self, path: str, default=None):
        return self.get_path(path, default)

    def set(self, path: str, val):
        return self.set_path(path, val)

    # TODO: Will be removed in 2.0
    def _get_path(self, path: str, default=None, mandatory=False):
        return self.get_path(path, default, mandatory)

    def get_path(self, path: str, default=None, mandatory=False):
        keys = path.split(".")
        data = self.data
        for key in keys:
            key = key.replace("_dot_", ".")
            if key == "[0]":
                if isinstance(data, Sequence):
                    if len(data) > 0:
                        data = data[0]
                    elif mandatory:
                        raise ValueError(f"could not find mandatory field {path}")
                    else:
                        return default
                else:
                    raise ValueError(
                        f"trying to get [0] in path {path} of non-sequence {type(data)}"
                    )
            elif key not in data:
                if mandatory:
                    raise ValueError(f"could not find mandatory field {path}")
                return default
            else:
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
    if isinstance(obj, str):
        return obj
    if isinstance(obj, Sequence) and not isinstance(obj, ListWrapper):
        return ListWrapper(obj)
    if isinstance(obj, Mapping) and not isinstance(obj, DictWrapper):
        return DictWrapper(obj)
    return obj


def pprint_map(map, indent="", file=None, use_quotes=False):
    if file is None:
        file = sys.stdout
    indent_step = "  "
    if isinstance(map, str):
        print(f"{indent}{map}", file=file)
        return
    elif isinstance(map, Sequence):
        for v in map:
            print(f"{indent}- {v}", file=file)
        return

    if map is None:
        logger.warning("No values present to print")
        return

    for key in sorted(map.keys()):
        val = map.get(key, None)
        if isinstance(val, Mapping):
            if len(val) == 0:
                print(f"{indent}{key}: " + "{}", file=file)
            else:
                print(f"{indent}{key}:", file=file)
                pprint_map(val, indent=indent + indent_step, file=file, use_quotes=use_quotes)
        elif isinstance(val, str):
            if use_quotes:
                print(f'{indent}{key}: "{val}"', file=file)
            else:
                print(f"{indent}{key}: {val}", file=file)
        elif isinstance(val, Sequence):
            print(f"{indent}{key}:", file=file)
            for v in val:
                print(f"{indent}- {v}", file=file)
        else:
            print(f"{indent}{key}: {val}", file=file)


def pprint_tuple(tup, prefix=None, delimiter=".", pattern=None):
    for item in sorted(tup, key=lambda x: x[0]):
        if prefix is None:
            print_filtered(f"{item[0]}={item[1]}", pattern)
        else:
            print_filtered(f"{prefix}{delimiter}{item[0]}={item[1]}", pattern)


def print_filtered(text, pattern):
    if pattern is not None:
        regex_pattern = re.compile(pattern, re.IGNORECASE)
        if regex_pattern.search(text):
            print(text)
    else:
        print(text)
