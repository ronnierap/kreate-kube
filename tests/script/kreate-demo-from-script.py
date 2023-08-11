#!/usr/bin/env python3
"""
This test script shows that you can kreate komponents from a python script.
The komponents will still be configured by the appdef.konfig.
You can also configure them further in python.
In general it is preferred to kreate all komponents from the konfig.
"""

from kreate.kore import AppDef, App, run_cli
import kreate.kube

def kreate_appdef(appdef_filename:str) -> AppDef:
    # ignore passed in appdef
    appdef = AppDef("tests/script/appdef.yaml")
    appdef.load_konfig_files()
    return appdef


def kreate_app(appdef: AppDef) -> App:
    app = kreate.kube.KustApp(appdef) # or appdef.kreate_app()?
    app.register_template_file("MyUdpService", kreate.kube.Resource, "templates/MyUdpService.yaml")
    app.kreate_komponent("MyUdpService", "main")

    kreate.kube.Ingress(app, "root")
    app.ingress.root.sticky()
    app.ingress.root.whitelist("10.20.30.40")
    app.ingress.root.basic_auth()
    app.ingress.root.label("dummy", "jan")
    kreate.kube.Ingress(app, "api")

    kreate.kube.Egress(app, "db")
    kreate.kube.Egress(app, "redis")
    kreate.kube.Egress(app, "xyz")

    depl=kreate.kube.Deployment(app)
    depl.pod_label("egress-to-db", "enabled")
    kreate.kube.HttpProbesPatch(app.depl.main)
    kreate.kube.AntiAffinityPatch(depl)
    kreate.kube.Service(app)
    app.service.main.headless()
    kreate.kube.Service(app, "https")


    pdb = kreate.kube.PodDisruptionBudget(app, name="demo-pdb")
    pdb.yaml.spec.minAvailable = 2
    pdb.label("testje","test")

    app.kreate_komponent("Secret", "main")
    app.kreate_komponent("ServiceAccount")
    app.kreate_komponent("ServiceMonitor")
    app.kreate_komponent("HorizontalPodAutoscaler")

    cm = kreate.kube.Kustomization(app)

    return app

run_cli(kreate_appdef, kreate_app)
