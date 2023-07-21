#!/usr/bin/env python3
import sys; sys.path.append(".")  # to find the kreate package from test subdir

import kreate

def demo_app():
    app = kreate.App('demo')

    ingr = kreate.Ingress(app)
    ingr.sticky()
    ingr.whitelist("ggg")
    ingr.basic_auth()
    ingr.add_label("dummy", "jan")

    depl = kreate.Deployment(app)
    depl.add_template_label("egress-to-oracle", "enabled")

    pdb = kreate.PodDisruptionBudget(app)
    pdb.yaml.spec.minAvailable = 2

    cm = kreate.ConfigMap(app)
    cm.add_var("ORACLE_URL")
    cm.add_var("ORACLE_USR")
    cm.add_var("ORACLE_SCHEMA")


    kust = kreate.Kustomization(app)

    app.kreate_resources()

kreate.cli(demo_app)
