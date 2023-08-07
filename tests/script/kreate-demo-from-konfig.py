#!/usr/bin/env python3
import kreate

def kreate_appdef(appdef_filename:str, env: str) -> kreate.AppDef:
    # ignore passed in appdef
    appdef = kreate.AppDef(env, "tests/script/appdef.yaml")
    appdef.kreate_app_func = kreate_app
    return appdef


def kreate_app(appdef: kreate.AppDef,) -> kreate.App:
    app = kreate.KustApp(appdef)
    app.kreate_from_config()
    return app

kreate.Cli(kreate_appdef).run()
