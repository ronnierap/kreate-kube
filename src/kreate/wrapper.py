from ruamel.yaml.comments import CommentedSeq
from collections import UserDict, UserList
from collections.abc import Mapping, Sequence

class DictWrapper(UserDict):
    def __init__(self, dict):
        # do not copy the original dict as the normal UserDict does
        # but wrap the original so that updates go to the original
        super().__setattr__("data", dict)

    def __getattr__(self, attr):
        if attr not in self.data:
            # TODO: more informative error message
            raise AttributeError(f"Yaml object does not have attribute {attr}")
        else:
            return wrap(self.data[attr])

    def __setattr__(self, attr, val):
        self.data[attr] = val


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

class LayeredMap():
    def __init__(self, dict):
        # do not copy the original dict as the normal UserDict does
        # but wrap the original so that updates go to the original
        super().__setattr__("data", dict)

    def __getattr__(self, attr):
        if attr not in self.data:
            # TODO: more informative error message
            raise AttributeError(f"Yaml object does not have attribute {attr}")
        else:
            return wrap(self.data[attr])





class DeepChain(Mapping):
    def __init__(self, map: Mapping, parent: Mapping):
        self._parent = parent
        self._map = map

    def __getitem__(self, key):
        val = self._map.get(key, None)
        pval = self._parent.get(key, None)
        if isinstance(val,Mapping) and isinstance(pval,Mapping):
            return DeepChain(val, pval)
        if isinstance(val,Mapping) or isinstance(pval,Mapping):
            raise AttributeError(f"key {key} is not mergeable for {type(val)} and {type(pval)}")
        return self._map.get(key, pval) # TODO will return None instead of attribute error


    def __getattr__(self, attr):
        if attr not in self:
            # TODO: more informative error message
            raise AttributeError(f"DeepChain object does not have attribute {attr}")
        else:
            return wrap(self[attr])

    def __len__(self):
        keys = { **self._map, **self._parent }
        return len(keys)

    def __iter__(self): # chain_from_iterable=chain.from_iterable
        keys = { **self._map, **self._parent }
        return iter(keys)

    def __contains__(self, key):
        if key in self._map:
            return True
        return key in self._parent

    def __repr__(self):
        return f"DeepChain({self._map},{self._parent})"
