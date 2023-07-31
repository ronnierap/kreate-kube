# kisst.kreate
kreate kubernetes/kustomize yaml files based on templates

The purpose of the kreate framework is to easily create
kubernetes resources for an application.
This is especially useful if you have many different applications
that you would like to keep as similar as possible,
while also having flexibility to tweak each application.

## Example using application structure file
We will use a simple script that loads an application structure file,
and generates all components from that file.

Note: this is still a rough design, and many details and names might
change in the near future
### kreate.py
The `kreate.AppStructure('demo')` command will create all components
```
#!/usr/bin/env python3
import kreate

def demo_app():
    app = kreate.AppStructure('demo')
    # It is possible to finetune the app object if needed

kreate.cli(demo_app)
```

The kreate py script can load config file(s), such as:
- `kreate-defaults.yaml`: default files for all kreate templates in kreate package
- `demo-app-struct.yaml`: high level application definition
- `demo-prd-values.yaml`: specific values for the prd (production) environment

### demo-app-structure.yaml
The structure file is a yaml describing in a high level which resources
are needed:
```
kind: Deployment/StatefulSet/CronJob
container:
  app:
    image: abc.app
    probePath: actuator/info
ingress:
  root:
    path: /
    sticky: True
  api:
    path: /api
    read-timeout: 60  # This always is a slow api, so it should be longer
egress: # dict to be mergable with fields, but bt ugly with all emtpyP{}
  db: {}
  redis: {}
  xyz: {}
vars: # just list what vars are required for the image to work
  - ENV
  - DB_URL
  - DB_SCHEMA
secrets:
  - DB_USR
  - DB_PSW
files:
  - application.properties
  - logging.properties
secret-files
  - certificate.key
```
These resources will be created using


## Simple using example
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
