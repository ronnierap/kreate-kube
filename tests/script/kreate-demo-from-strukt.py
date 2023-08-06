#!/usr/bin/env python3
import kreate

def kreate_appdef(appdef:str, env: str) -> kreate.AppDef:
    # ignore passed in appdef
    appdef = kreate.AppDef(env, "tests/script/appdef-extras.yaml")
    #appdef.app_class = kreate.KustApp
    return appdef


#def kreate_app(appdef:str, env: str) -> kreate.App:
#    app_cfg = kreate_config(appdef, env)
#    app = kreate.KustApp(app_cfg, env)
#    app.kreate_from_config()
#    return app

kreate.run_cli(kreate_appdef)
