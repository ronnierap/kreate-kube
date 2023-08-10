import kreate

def kreate_appdef(appdef_filename:str) -> kreate.AppDef:
    appdef = kreate.AppDef(appdef_filename)
    return appdef

def kreate_app(appdef: kreate.AppDef) -> kreate.App:
    appdef.load_konfig_files()
    app = appdef.kreate_app()
    app.konfigure_from_konfig()
    return app


kreate.run_cli(kreate_appdef, kreate_app)
