#!/usr/bin/env python3
import kreate

def kreate_appdef(appdef:str, env: str) -> kreate.AppDef:
    # ignore passed in appdef
    appdef = kreate.AppDef(env, "tests/script/appdef.yaml")
    #appdef.app_class = kreate.KustApp
    return appdef

kreate.run_cli(kreate_appdef)
