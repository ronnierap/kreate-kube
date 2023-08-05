import kreate

def kreate_appdef(appdef:str, env: str) -> kreate.AppDef:
    appdef = kreate.AppDef(env, appdef )
    appdef.app_class = kreate.KustApp
    return appdef



kreate.run_cli(kreate_appdef)
