import kreate

def kreate_config(appdef:str, env: str) -> kreate.AppDef:
    return kreate.AppDef(env, appdef )

def kreate_app(appdef:str, env: str) -> kreate.App:
    app_cfg = kreate_config(appdef, env)
    app = kreate.KustApp(app_cfg, env)
    app.kreate_from_config()
    return app

kreate.run_cli(kreate_app)
