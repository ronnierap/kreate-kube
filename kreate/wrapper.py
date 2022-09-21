

class DictWrapper():
    def __init__(self, somedict) -> None:
        self._dict = somedict

    def __getattr__(self, attr):
        if attr in self.__dict__ or attr=="_dict":
            return super().__getattribute__(attr)
        result = self._dict[attr]
        if isinstance(result, dict):
            return DictWrapper(result)
        return result

    def add(self, key, value):
        self._dict[key]=value

    def get(self, key):
        return self._dict[key]

    def __setattr__(self, attr, val):
        if attr in self.__dict__ or attr=="_dict":
            return super().__setattr__(attr, val)
        self._dict[attr]=val
