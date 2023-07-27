#!/usr/bin/env python3
import kreate.yaml
from kreate.wrapper import wrap
import copy

a={
    "a": 1,
    "b": {
        "b1": 1,
        "b2": 2,
    }
}


b={
    "a": 1,
    "b": {
        "b2": 22,
        "b3": 3
    },
    "c": 33
}


wa=wrap(copy.deepcopy(a))
wb=wrap(b)

print(wb.c)
kreate.yaml.merge(a,b)
print (a)


kreate.yaml.merge(wa,wb)
print (wa)
print(a)
