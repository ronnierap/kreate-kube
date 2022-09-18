#!/usr/bin/env python3

import kreate
import kreate.file

env=kreate.Environment('acc')
app=kreate.App('cls', env)
app.container[0].image_version="1.2.3"

app.labels["egress-to-oracle"]="enabled"

kreate.file.deployment(app, env)
