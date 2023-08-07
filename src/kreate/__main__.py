import kreate

def kreate_appdef(appdef_filename:str, env: str) -> kreate.AppDef:
    appdef = kreate.AppDef(env, appdef_filename)
    return appdef



kreate.Cli(kreate_appdef).run()
