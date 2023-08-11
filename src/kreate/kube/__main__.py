from ..kore import AppDef, App

from . import KubeCli
from . import KustApp

def kreate_appdef(appdef_filename:str) -> AppDef:
    appdef = AppDef(appdef_filename)
    return appdef

def kreate_app(appdef: AppDef) -> App:
    appdef.load_konfig_files()
    app = KustApp(appdef)
    app.konfigure_from_konfig()
    return app

KubeCli().run(kreate_appdef, kreate_app)
