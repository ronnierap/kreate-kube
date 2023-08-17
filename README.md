# kreate-kube
kreate kubernetes/kustomize yaml files based on templates

The purpose of the kreate-kube framework is to easily create
kubernetes resources for an application.
This is especially useful if you have many different applications
that you would like to keep as similar as possible,
while also having flexibility to tweak each application.

## Example using application structure file
Kreating resources is based on a application strukture definition file.
Usually there are ate least 3 files needed for a setup:
- `konfig.yaml`  ties all together
- `<app>-strukture.yaml`  describes the structure of all application components
- `values-<app>-<env>.yaml`  contains specific values for a certain environment
Note that these filename may be changed.

### demo-strukture.yaml
The structure file is a yaml describing in a high level which resources
are needed:
```
Deployment:
  main:
    vars:
    - demo-vars
    secret-vars:
    - demo-secrets
    patches:
      AntiAffinityPatch: {}
      HttpProbesPatch: {}
      AddEgressLabelsPatch: {}

Egress:
  db:
    name: egress-to-db
    cidr_list: {{ val.db_egress_cidr_list }}
    port: {{ val.db_port }}

Ingress:
  all:
    host: {{ val.ingress_host_internal }}
    path: /
    options:
      - basic_auth

Kustomization:
  main:
    configmaps:
      demo-vars:
        vars:
          ENV: {{ val.env }}
          DB_URL: {{ val.DB_URL }}

Secret:
  main:
    name: demo-secrets
    vars:
      DB_PSW: {{ val.DB_PSW | dekrypt() }}
      DB_USR: {{ val.DB_USR }}

SecretBasicAuth:
  basic-auth:
    users:
      - admin
      - guest

Service:
  main:
    name: demo-service
```
Note: This shows only a small subset of possibilities of kreate-kube

### konfig.yaml
```
{% set appname = "cls" %} # reuse the appname in rest of this file
{% set env = "acc" %} # reuse the appname in rest of this file
values:
  appname: {{ appname }}
  env: {{ env }}
  team: knights
  project: kreate-kube-demo
  image_version: 2.0.2

value_files:
  - values-{{appname}}-{{env}}.yaml
strukture_files:
  - py:kreate.kube.templates:default-values.yaml
  - {{appname}}-strukture.yaml
```


## Using a minimal python script
The strukture file above is always needed, and usually it should be all you need.
However originally `kreate` was more script based (originally even bash scripts).
It is still possible to use a script and there might be cases where you need to finetune some things
that can only be done in Python.
### kreate-demo.py
```
#!/usr/bin/env python3

from kreate.kore import Konfig, App
from kreate.kube import KustApp, KubeKreator

def kreate_app(konfig: Konfig) -> App:
    app = KustApp(konfig)
    app.kreate_komponents_from_strukture()
    app.aktivate()

    # Start finetuning the yaml komponents
    # Note: adding a custom label does not require python
    app.depl.main.label("custom-label","added-by-script")
    return app

KubeKreator(kreate_app).kreate_cli().run()
```

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
