#!/usr/bin/env python3

import kreate

app = kreate.App('demo')
app.labels["egress-to-oracle"] = "enabled"

env = kreate.Environment('acc', app)
env.project = "kreate-test"


kust = kreate.Kustomization(app)

ingr = kust.add(kreate.Ingress(app, sticky=True))
ingr.whitelist("ggg")
ingr.basic_auth()

depl=kust.add(kreate.Deployment(app))
depl.container[0].image_version = "1.2.3"


kust.kreate(env)
