#!/usr/bin/env python3

import kreate.App
import kreate.Environment
import kreate.Ingress
import kreate.file

env = kreate.Environment('acc')
env.project = "kreate-test"

app = kreate.App('cls', env)
app.container[0].image_version = "1.2.3"
app.labels["egress-to-oracle"] = "enabled"

ingr = kreate.Ingress(app, sticky=True)
print(ingr.name)
ingr.whitelist("ggg")
ingr.basic_auth()
ingr.kreate()

# kreate.file.deployment(app)
