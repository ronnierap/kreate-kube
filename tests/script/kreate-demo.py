#!/usr/bin/env python3
import kreate
import appdef

def kreate_demo_app(env: str):
    cfg = kreate.core.Config()
    cfg._values.add_obj(appdef)
    cfg._values.add_yaml(f"tests/script/values-{env}.yaml")
    cfg.add_files(
        f"tests/script/config-demo-{env}.yaml",
        "tests/script/config-demo.yaml",
        "src/kreate/templates/default-values.yaml",
        )

    app = kreate.App('demo', env, kustomize=True, config=cfg)

    kreate.Ingress(app)
    app.ingress.root.sticky()
    app.ingress.root.whitelist("ggg")
    app.ingress.root.basic_auth()
    app.ingress.root.add_label("dummy", "jan")
    kreate.Ingress(app, "api", path="/api")

    kreate.Egress(app, "db")
    kreate.Egress(app, "redis")
    kreate.Egress(app, "xyz")

    depl=kreate.Deployment(app)
    depl.add_template_label("egress-to-db", "enabled")
    kreate.HttpProbesPatch(depl)
    kreate.AntiAffinityPatch(depl)
    kreate.Service(app)
    app.service._.headless()

    pdb = kreate.PodDisruptionBudget(app)
    pdb.yaml.spec.minAvailable = 2
    pdb.add_label("testje","test")

    app.kreate("ServiceAccount")
    app.kreate("ServiceMonitor")

    cm = kreate.ConfigMap(app, "vars", name="demo-vars", kustomize=False)
    cm.add_var("ENV", value=app.env)
    cm.add_var("ORACLE_URL")
    cm.add_var("ORACLE_USR")
    cm.add_var("ORACLE_SCHEMA")

    return app

kreate.run_cli(kreate_demo_app)
