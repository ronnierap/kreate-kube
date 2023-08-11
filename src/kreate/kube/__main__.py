from ..kore import AppDef, App

from . import KubeCli
from . import KustApp
from ..krypt import _krypt
from ..kore import _app

def kreate_appdef(appdef_filename:str) -> AppDef:
    return AppDef(appdef_filename)

def kreate_app(appdef: AppDef) -> App:
    app = KustApp(appdef)
    app.konfigure_from_konfig()
    return app

KubeCli().run(kreate_appdef, kreate_app)
