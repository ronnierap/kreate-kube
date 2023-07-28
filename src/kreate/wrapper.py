from ruamel.yaml.comments import CommentedSeq
from collections import UserDict
from collections.abc import Mapping, Sequence

class DictWrapper(UserDict):
    def __init__(self, dict):
        super().__setattr__("data", dict)

    def __getattr__(self, attr):
        if attr in self.__dict__ or attr=="data":
            return super().__getattribute__(attr)
        #print(f"getting {attr}")
        if attr not in self.data:
            print(f"emtpy attr  {attr}")
            return wrap({}) # TODO
        else:
            return wrap(self.data[attr])

    def __setattr__(self, attr, val):
        #print(f"###setting {attr} to [{val}]")
        if attr in self.__dict__ or attr == "data":
            return super().__setattr__(attr, val)
        self.data[attr] = val

#    def add(self, key, value):
#        print(f"called add {key} [{value}]")
#        self.data[key] = wrap(value)
#        print("done")
#
#    def get(self, key):
#        return self.data[key]


class ListWrapper():
    def __init__(self, seq) -> None:
        self._seq = seq

    def __getitem__(self, idx):
        return wrap(self._seq[idx])

    def __setitem__(self, idx, val):
        self._seq[idx] = val

    def append(self, item):
        self._seq.append(item)


def wrap(obj):
    if isinstance(obj, Sequence) and not isinstance(obj, ListWrapper):
        return ListWrapper(obj)
    if isinstance(obj, Mapping) and not isinstance(obj, DictWrapper):
        return DictWrapper(obj)
    return obj
