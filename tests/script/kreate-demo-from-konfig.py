#!/usr/bin/env python3
"""
This test script shows that you can kreate komponents from konfig file.
After this you can fientune them further in python.
In general it is preferred to not use a script but use `python3 -m kreate`
"""

import kreate.kore
import kreate.kube


def kreate_appdef(appdef_filename:str) -> kreate.kore.AppDef:
    # ignore passed in appdef
    appdef = kreate.kore.AppDef("tests/script/appdef.yaml")
    appdef.load_konfig_files()
    return appdef

def kreate_app(appdef: kreate.kore.AppDef) -> kreate.kore.App:
    appdef.load_konfig_files()
    app = kreate.kube.KustApp(appdef)
    app.konfigure_from_konfig()
    # find the (main) Deployment and modify it a bit
    app.depl.main.label("this-is-added","by-script")
    return app

kreate.kube.KubeCli().run(kreate_appdef, kreate_app)
