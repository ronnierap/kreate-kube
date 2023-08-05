import kreate

def kreate_appdef(appdef_filename:str, env: str) -> kreate.AppDef:
    appdef = kreate.AppDef(env, appdef_filename )
    appdef.app_class = kreate.KustApp
    return appdef



kreate.run_cli(kreate_appdef)
