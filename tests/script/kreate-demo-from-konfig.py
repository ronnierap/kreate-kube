#!/usr/bin/env python3
"""
This test script shows that you can kreate komponents from konfig file.
After this you can fientune them further in python.
In general it is preferred to not use a script but use `python3 -m kreate`
"""

import kreate

def kreate_appdef(appdef_filename:str, env: str) -> kreate.AppDef:
    # ignore passed in appdef
    appdef = kreate.AppDef(env, "tests/script/appdef.yaml")
    appdef.kreate_app_func = kreate_app
    return appdef


def kreate_app(appdef: kreate.AppDef) -> kreate.App:
    app = kreate.KustApp(appdef)
    app.kreate_from_konfig()
    # find the (main) Deployment and modify it a bit
    app.depl.main.label("this-is-added","by-script")
    return app

kreate.Cli(kreate_appdef).run()