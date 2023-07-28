#!/usr/bin/env python3
import kreate.yaml
from kreate.wrapper import wrap, DeepChain
import copy
from collections import ChainMap
from collections.abc import Mapping

a={
    "a": 1,
    "b": {
        "b1": 1,
        "b2": 2,
    }
}


b={
    "b": {
        "b2": 22,
        "b3": 3
    },
    "c": 33
}

wa=wrap(copy.deepcopy(a))
wb=wrap(b)

#print(wa)
#print(wb)
c=DeepChain(wb,wa)

print(f"a={c.a}")
print(f"b={c.b}")
print(f"b.b1={c.b.b1}")
print(f"b.b2={c.b.b2}")
print(f"b.b3={c.b.b3}")
print(f"len(b)={len(c.b)}")
for k in c.b.keys():
    print(k)

print("\n\n\n")

print (a)
print (b)
kreate.yaml.merge(a,b)
print (a)
print("\n\n\n")

print (wa)
print (wb)
kreate.yaml.merge(wa,wb)
print (wb)