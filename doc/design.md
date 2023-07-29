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

## config structure
```
trigger: cron?, service, queue
replicas: fixed, hpa, stateful
ingress:
  root:
    context-root: "/foo"
    basic-auth:
      auth-file: "secrets/auth"
  api:
    read-timeout: 300  # On this environment it is even slower
egress:
  db:
    hosts: {{ shared.oracle.hosts }}
    port: 1521
  redis: None?
  xyz:
    hosts: {{ shared.xyz.hosts }}
    port: 8080
vars:
  ENV: {{ app.env }}
  DB_URL: {{ oracle_cn('db_svc123') }}
  DB_SCHEMA: 'my_schema'
  DB_USR: 'my_usr'
  DB_PSW: {{ dekrypt(secrets.db_psw) }}
  XYZ_URL: {{ shared.xyz.url }}
```
template data:
- app?
- vars
- shared
-
