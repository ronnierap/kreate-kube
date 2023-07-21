from ruamel.yaml.comments import CommentedSeq


class DictWrapper():
    def __init__(self, somedict) -> None:
        self._dict = somedict

    def __getattr__(self, attr):
        if attr in self.__dict__ or attr == "_dict":
            return super().__getattribute__(attr)
        return wrap(self._dict[attr])

    def add(self, key, value):
        self._dict[key] = value

    def get(self, key):
        return self._dict[key]

    def has_key(self, key) -> bool:
        return key in self._dict

    def __setattr__(self, attr, val):
        if attr in self.__dict__ or attr == "_dict":
            return super().__setattr__(attr, val)
        self._dict[attr] = val


class SeqWrapper():
    def __init__(self, seq) -> None:
        self._seq = seq

    def __getitem__(self, idx):
        return wrap(self._seq[idx])

    def __setitem__(self, idx, val):
        self._seq[idx] = val

    def append(self, item):
        self._seq.append(item)


def wrap(result):
    if isinstance(result, CommentedSeq):
        return SeqWrapper(result)
    if isinstance(result, dict):
        return DictWrapper(result)
    return result
