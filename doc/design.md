# Design

- it should be very easy to support common applications (sane defaults)
- it should be easy to tweak certain settings
- it should be easy to extend or support differing configurations

# Rough flow
1. create App object
   - init config values
     - global kreate defaults
     - app values
     - environment values
2. kreate resources
   - parse jinja template with config-values, resource specific values
   - modify yaml (directly or with convenience methods)
   - add patches (nginx sidecar)
3. create files from App object (or kustomize)
4. run kubectl

config vlaues: yaml format?
resemble kubernetes

# Intended file layout
- requirements.txt: pin dependencies
  * kreate version
  * extra templates
  * shared config
- setup.sh/bat: init python
- kreate-<app>.py: main script
- app-structure.yaml
- config-defaults.yaml
- env/<env>/: scripts, values and files for a specific enviroment:
  - custom.py
  - config-overrides
  - egress-defs
  - ingress-defs
  - var-values
  - secret-values
  - files
  - secret-files


## app-structure.yaml
This file describes high level what the application needs to have.
It does not provide any environment specific values, just high level structure
```
kind: Deployment/StatefulSet/CronJob
image: abc.app
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
vars: # list to just list what is required (for the image to work)
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
  - cert.key
```

## konfig structure
```
app:
  appname: demo
  env: dev
  team: knights
  image_version: 4.0.1
  namespace: demo-dev
inklude:
  - framework:init-dev.konf
requires:
  kreate-kube: 0.4.0
  shared_templates: v1.3
  shared_konfig: v1.4
templates:
  kool_templates:/kool_templates.konf
  shared_templates:/shared_templates.konf


# These should be defined in inkludes
vars:
  ... # from inklude file
values:
  ... # from inklude file
secrets:
  ... # from inklude file
files:
  default.conf: ./dev/files/default.conf
  logback.xml: shared_konfig:/generic-logback.xml
secret-files:
  private.key: dekrypt:shared_konfig:/dev/secret-files/private.key.encrypted


# in framework/init-dev.konf
# Note extra inkludes in a inklude need to add/rerun inklude...
inklude:
  - shared_templates:shared_templates.konf
  - shared_konfig:dev/shared_values-dev.konf
  - inklude_path:values-demo-dev.konf
  - inklude_path:vars-demo-dev.konf
  - inklude_path:secrets-demo-dev.konf
  - inklude_path:files-demo-dev.konf
settings:
  inklude_path: .:./dev  # ./dev
  sources:
    kreate-kube: pip # cannot be installed, since python is already running
    # an archive url for github
    kool_templates: https://github.com/MarkHooijkaas/kool_templates/archive/{{requires.kool_templates}}.zip
    # archive urls for company hosted bitbucket

    shared_templates: https://{{USR}}:{{PSW}}@bitbucket.company.org/rest/api/latest/projects/{{BITBUCKET_PROJECT}}/repos/shared_templates/archive?at={{requires["shared_templates"]}}&format=zip
    shared_konfig: https://{{USR}}:{{PSW}}@bitbucket.company.org/rest/api/latest/projects/{{BITBUCKET_PROJECT}}/repos/shared_konfig/archive?at={{requires.["shared_konfig"]}}&format=zip

```
template data:
- app
- var
- value
- secret
- my
  - konfig
  - app
  - vars
  - values
