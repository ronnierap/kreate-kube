from ..kore import AppDef, App
from . import KubeKreator
from . import KustApp


#def kreate_appdef(appdef_filename: str) -> AppDef:
#    return AppDef(appdef_filename)


def kreate_app(appdef: AppDef) -> App:
    app = KustApp(appdef)
    app.kreate_komponents_from_strukture()
    app.aktivate()
    return app


KubeKreator().kreate_cli().run(kreate_app)
