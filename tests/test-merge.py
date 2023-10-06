#!/usr/bin/env python3
from kreate._core import wrap, DeepChain, merge
import copy

a = {
    "a": 1,
    "b": {
        "b1": 1,
        "b2": 2,
    },
}


b = {"b": {"b2": 22, "b3": 3}, "c": 33}

wa = wrap(copy.deepcopy(a))
wb = wrap(b)

# print(wa)
# print(wb)
c = DeepChain(wb, wa)
print(c.keys())
print(type(c.b))
print(c.b)
print(c.b.keys())
print(f"a={c.a}")
print(f"b={c.b}")
print(f"b.b1={c.b.b1}")
print(f"b.b2={c.b.b2}")
print(f"b.b3={c.b.b3}")
print(f"len(b)={len(c.b)}")
for k in c.b.keys():
    print(k)

print("\n\n\n")

print(a)
print(b)
merge(a, b)
print(a)
print("\n\n\n")

print(wa)
print(wb)
merge(wa, wb)
print(wb)
