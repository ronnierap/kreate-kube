#!/usr/bin/env python3
"""
This test script shows that you can kreate komponents from a python script.
The komponents will still be configured by the appdef.konfig.
You can also configure them further in python.
In general it is preferred to kreate all komponents from the konfig.
"""
import kreate

def kreate_appdef(appdef_filename:str, env: str) -> kreate.AppDef:
    # ignore passed in appdef
    appdef = kreate.AppDef(env, "tests/script/appdef.yaml")
    appdef.load_konfig_files()
    return appdef


def kreate_app(appdef: kreate.AppDef) -> kreate.App:
    app = kreate.KustApp(appdef) # or appdef.kreate_app()?
    app.register_template_file("MyUdpService", kreate.Resource, "templates/MyUdpService.yaml")
    app.kreate_komponent("MyUdpService", "main")

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

    app.kreate_komponent("Secret", "main")
    app.kreate_komponent("ServiceAccount")
    app.kreate_komponent("ServiceMonitor")
    app.kreate_komponent("HorizontalPodAutoscaler")

    cm = kreate.Kustomization(app)

    return app

kreate.run_cli(kreate_appdef, kreate_app)
