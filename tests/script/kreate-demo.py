#!/usr/bin/env python3
import kreate

def kreate_config(appdef:str, env: str) -> kreate.AppDef:
    # ignore passed in appdef
    return kreate.AppDef(env, "tests/script/appdef.yaml")

def kreate_app(appdef:str, env: str) -> kreate.App:
    app_cfg = kreate_config(appdef, env)
    app = kreate.KustApp(app_cfg, env)

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

    cm = kreate.ConfigMap(app, "vars") # kustomize=False
    cm.add_var("ENV", app.values["env"])
    cm.add_var("ORACLE_URL")
    cm.add_var("ORACLE_USR")
    cm.add_var("ORACLE_SCHEMA")

    return app

kreate.run_cli(kreate_app)
