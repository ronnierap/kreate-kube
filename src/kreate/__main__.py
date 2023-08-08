import kreate

def kreate_appdef(appdef_filename:str, env: str) -> kreate.AppDef:
    appdef = kreate.AppDef(env, appdef_filename)
    return appdef

def kreate_app(appdef: kreate.AppDef) -> kreate.App:
    appdef.load_extra()
    app = appdef.kreate_app()
    app.konfigure_from_konfig()
    return app


kreate.Cli(kreate_appdef, kreate_app).run()
