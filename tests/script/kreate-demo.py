#!/usr/bin/env python3
import kreate

def kreate_appdef(appdef_filename:str, env: str) -> kreate.AppDef:
    # ignore passed in appdef
    appdef = kreate.AppDef(env, "tests/script/appdef.yaml")
    appdef.kreate_app_func = kreate_app
    return appdef


def kreate_app(appdef: kreate.AppDef,) -> kreate.App:
    app = kreate.KustApp(appdef)

    kreate.Ingress(app, "root")
    app.ingress.root.sticky()
    app.ingress.root.whitelist("10.20.30.40")
    app.ingress.root.basic_auth()
    app.ingress.root.label("dummy", "jan")
    kreate.Ingress(app, "api")

    kreate.Egress(app, "db")
    kreate.Egress(app, "redis")
    kreate.Egress(app, "xyz")

    depl=kreate.Deployment(app)
    depl.pod_label("egress-to-db", "enabled")
    kreate.HttpProbesPatch(app.depl.main)
    kreate.AntiAffinityPatch(depl)
    kreate.Service(app)
    app.service.main.headless()
    kreate.Service(app, "https")


    pdb = kreate.PodDisruptionBudget(app, name="demo-pdb")
    pdb.yaml.spec.minAvailable = 2
    pdb.label("testje","test")

    app.kreate_resource("ServiceAccount")
    app.kreate_resource("ServiceMonitor")
    app.kreate_resource("HorizontalPodAutoscaler")

    cm = kreate.KustConfigMap(app, "vars") # kustomize=False
    cm.add_var("ENV", app.values["env"])
    cm.add_var("ORACLE_URL")
    cm.add_var("ORACLE_USR")
    cm.add_var("ORACLE_SCHEMA")

    return app

kreate.Cli(kreate_appdef).run()
