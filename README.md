# kreate-kube
kreate kubernetes/kustomize yaml files based on templates

The purpose of the kreate framework is to easily create
kubernetes resources for an application.
This is especially useful if you have many different applications
that you would like to keep as similar as possible,
while also having flexibility to tweak each application.

## Simple example using python script
This script creates different python objects that can be deployed to kubernetes
For simplpicity sake, it does not show more extensive configuration
```
#!/usr/bin/env python3
import kreate

def kreate_demo_app():
    app = kreate.App('demo', kustomize=True)

    root=kreate.Ingress(app)  # create a root ingress object and remember it in var root
    root.sticky()       # fine tune the root ingress by adding session affinity
    root.basic_auth()   # fine tune the root ingress by adding basic authentication

    kreate.Ingress(app, path="/api", name="api")  # kreate a second ingress that needs no tuning

    kreate.Deployment(app)
    # alternative syntax `app.depl` to get the deployment from the app for finetuning
    app.depl.add_template_label("egress-to-oracle", "enabled")

    # kreate some (kustomize patches on the deployment)
    kreate.HttpProbesPatch(app.depl)
    kreate.AntiAffinityPatch(app.depl)

    kreate.Service(app)

    kreate.PodDisruptionBudget(app, name="demo-pdb")
    app.pdb.yaml.spec.minAvailable = 2
    app.pdb.add_label("testje","test")

    kreate.ConfigMap(app, name="demo-vars")
    app.cm.add_var("ENV", value=app.config["env"])
    app.cm.add_var("ORACLE_URL")
    app.cm.add_var("ORACLE_USR")
    app.cm.add_var("ORACLE_SCHEMA")

    return app

kreate.run_cli(kreate_demo_app)
```

## Example using application structure file
The Python objects in the above script are the basis for the kreating resources
based on a application strukture definition file.

We will use a simple script that loads an application structure file,
and generates all components from that file.

Note: this is still a rough design, and many details and names might
change in the near future
### kreate.py
```
#!/usr/bin/env python3
import kreate

def demo_app():
    app = kreate.AppStructure('demo')
    # It is possible to finetune the app object if needed

kreate.cli(demo_app)
```
The `kreate.AppStructure('demo')` command will create all components, described in a
`demo-app-structure.yaml` file with configuration/tuning from several config files,
that can be load automatically, such as:
- `kreate-defaults.yaml`: default files for all kreate templates in kreate package
- `demo-app-struct.yaml`: high level application definition
- `demo-prd-values.yaml`: specific values for the prd (production) environment
All these files are automatically loaded based on the application name (demo)
and the environment variable (prd)

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
egress: # dict to be mergable with fields, but bit ugly with all emtpy {}'s
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



## History
This is a rewrite of a similar project written as bash scripts.
The bash scripts have been used for deploying over 30 applications to
development, acceptance and production environments.

However the bash scripting language was not the best choice, so Python was chosen
for several reasons:
- Large bash scripts are difficult to maintain
  - google coding guidelines demand that bash scripts over 100 lines long are to be rewritten in Python.
    See https://google.github.io/styleguide/shellguide.html#when-to-use-shell, which states:
    > if you are writing a script that is more than 100 lines long, or that uses non-straightforward control flow logic,
    > you should rewrite it in a more structured language now.
    > Bear in mind that scripts grow.
    > Rewrite your script early to avoid a more time-consuming rewrite at a later date.
  - not many devops team members are proficient in bash
  - no OO and limited var scoping (most vars are global vars)
- Possibility to run natively on Windows (with Python installed)
  - no CRLF problems
  - Windows can recognizes `*.py` extension to prevent Linux file permission problems on Windows filesystems
- Much cleaner code
  - yaml parser
  - jinja templates
  - modular design
  - powerful requirements.txt/pip dependency management
