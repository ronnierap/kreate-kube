#!/usr/bin/env python3

import kreate

env = kreate.Environment('acc')
env.project = "kreate-test"

app = kreate.App('demo', 'v1.2', env)
app.labels["egress-to-oracle"] = "enabled"


kust = kreate.Kustomization(app)

ingr = kust.add(kreate.Ingress(app, sticky=True))
ingr.whitelist("ggg")
ingr.basic_auth()

depl = kust.add(kreate.Deployment(app))
pdb = kust.add(kreate.PodDisruptionBudget(app))
pdb.yaml.spec.minAvailable = 2

kust.kreate()
