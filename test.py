#!/usr/bin/env python3

import kreate.App
import kreate.Environment
import kreate.file

env = kreate.Environment('acc')
env.project = "kreate-test"

app = kreate.App('cls', env)
app.container[0].image_version = "1.2.3"

app.labels["egress-to-oracle"] = "enabled"

kreate.file.deployment(app, env)
