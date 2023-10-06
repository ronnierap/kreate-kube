"""
a chain of maps where an attribute will be checked in any of the maps
"""

from collections.abc import Mapping

# from typing import Mapping


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
