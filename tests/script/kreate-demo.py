#!/usr/bin/env python3
import kreate
import appdef

def kreate_demo_app(env: str):
    cfg = kreate.core.Config()
    cfg._values.add_obj(appdef)
    cfg._values.add_yaml(f"tests/script/values-{env}.yaml")
    cfg.add_files(
        f"tests/script/config-demo-{env}.yaml",
        "tests/script/demo-strukt.yaml",
        "src/kreate/templates/default-values.yaml",
        )

    app = kreate.App('demo', env, kustomize=True, config=cfg)

    kreate.Ingress(app)
    app.ingress.root.sticky()
    app.ingress.root.whitelist("ggg")
    app.ingress.root.basic_auth()
    app.ingress.root.add_label("dummy", "jan")
    kreate.Ingress(app, "api")

    kreate.Egress(app, "db")
    kreate.Egress(app, "redis")
    kreate.Egress(app, "xyz")

    depl=kreate.Deployment(app)
    depl.add_template_label("egress-to-db", "enabled")
    kreate.HttpProbesPatch(depl)
    kreate.AntiAffinityPatch(depl)
    kreate.Service(app)
    app.service.main.headless()
    kreate.Service(app, "https")


    pdb = kreate.PodDisruptionBudget(app)
    pdb.yaml.spec.minAvailable = 2
    pdb.add_label("testje","test")

    app.kreate("ServiceAccount")
    app.kreate("ServiceMonitor")
    app.kreate("HorizontalPodAutoscaler")

    cm = kreate.ConfigMap(app, "main", name="demo-vars", kustomize=True)
    cm.add_var("ENV", app.values["env"])
    cm.add_var("ORACLE_URL")
    cm.add_var("ORACLE_USR")
    cm.add_var("ORACLE_SCHEMA")

    return app

kreate.run_cli(kreate_demo_app)
