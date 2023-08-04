#!/usr/bin/env python3
import kreate

def kreate_config(appdef:str, env: str) -> kreate.AppDef:
    # ignore passed in appdef
    return kreate.AppDef(env, "tests/script/appdef-extras.yaml")

def kreate_app(appdef:str, env: str) -> kreate.App:
    app_cfg = kreate_config(appdef, env)
    app = kreate.App(app_cfg, env)
    app.kreate_from_config()
    return app

kreate.run_cli(kreate_app)
