#!/usr/bin/env python3
"""
This test script shows that you can kreate komponents from strukture file.
After this you can finetune them further in python.
In general it is preferred to not use a script but use `python3 -m kreate`
"""

from kreate.kore import AppDef, App
from kreate.kube import KustApp, KubeKreator

def kreate_app(appdef: AppDef) -> App:
    app = KustApp(appdef)
    app.kreate_komponents_from_strukture()
    app.aktivate()
    app.depl.main.label("this-is-added","by-script")
    return app

kreator = KubeKreator()
kreator.set_appdef_file("tests/demo/appdef.yaml")
kreator.kreate_cli().run(kreate_app)
