#!/usr/bin/env python3

import kreate

env = kreate.Environment('acc')
env.project = "kreate-test"

app = kreate.App('cls', env)
app.container[0].image_version = "1.2.3"
app.labels["egress-to-oracle"] = "enabled"

kust = kreate.Kustomization(app)

ingr = kust.add(kreate.Ingress(app, sticky=True))
ingr.whitelist("ggg")
ingr.basic_auth()

kust.add(kreate.Deployment(app))

kust.kreate()
