from ..kore import AppDef, App
from . import KubeCli
from . import KustApp


def kreate_appdef(appdef_filename: str) -> AppDef:
    return AppDef(appdef_filename)


def kreate_app(appdef: AppDef) -> App:
    app = KustApp(appdef)
    app.kreate_komponents_from_strukture()
    app.aktivate()
    return app


KubeCli().run(kreate_appdef, kreate_app)
