# kreate-core
kreate kubernetes/kustomize yaml files based on templates

The purpose of the kreate framework is to easily create
kubernetes resources for an application.
This is especially useful if you have many different applications
that you would like to keep as similar as possible,
while also having flexibility to tweak each application.

## Simple example
```
#!/usr/bin/env python3
import kreate

def demo_app():
    app = kreate.App('demo')

    kreate.Ingress(app)
    kreate.Ingress(app, path="/api", name="api")

    depl = kreate.Deployment(app)
    kreate.HttpProbes(depl)

    kreate.PodDisruptionBudget(app)

    cm = kreate.ConfigMap(app)
    cm.add_var("ORACLE_URL")
    cm.add_var("ORACLE_USR")
    cm.add_var("ORACLE_SCHEMA")

    kust = kreate.Kustomization(app)
    kust.kreate_files()

kreate.cli(demo_app)
```

## History
This is a rewrite of a similar project written as bash scripts
