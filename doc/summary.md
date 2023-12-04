# Summary
A deployment is described in a YAML document that can be split over multiple files,
that are merged into one YAML document.
This YAML is called a `konfig`, a configuration with a `k` for `k`ubernetes and `k`ustomize.

The YAML has several sections for different purposes:
- app: high level information about the app, such as the name and environment
- strukt: high level elements that should be created
- val: values like IP addresses that are needed for the components
- var: variables that are meant to be put in a Kubernetes ConfigMap
- secret: secret values and vars, that should be stored in encrypted format
- inklude: files that will be merged into the YAML document
- version: version information of files that can be used or inkluded
- system:
  - repo: repositories where (shared) konfig files and templates can be located
  - templates: definitions of templates that can be used

## app
This section is small, although you can put in anything you want.
kreate does require an appname and env in most cases
```yaml
app:
  appname: demo
  env: prd
  team: knights
version:
  app_version: 2.0.4
```

## strukt
This is the main section where you create komponents that will result in files that are kreated.
Komponents are identified by an id that is usually of the form `<klass>.<name>`
- klass: this is often a template name, that is the name of a kubernetes resource, e.g. Deployment or Ingress
- short_name: this is to have multiple instances of the same kind. Often there is only one and then main is used
Examples:
```yaml
strukt:
  Deployment:
    main:
      ...
  Egress:
    mysql: ...
    redis: ...
    kafka: ...
```
The komponents try to use sane defaults (which can be tuned).
This often leads that there is nothing to specify for a komponent.
This can be abbreviated by using the empty dictionar in yaml, like:
```yaml
strukt:
  Service:
    main: {}
```
In the example above it means a Service resource file will be kreated
with default behaviour.

This example can be simplified even further when there is only one komponent.
If a kind has no sub elements it is assumed to have just one `main` element
So the example above can even be abbreviated to:
```yaml
strukt:
  Service: {}
```
Indicating a default Service should be generated

## val and var
These are the main elements to tune the komponents.
`kreate` makes a distinction between `val` and `var`
- `val`: These can be used at all kind of different places, e.g.
  - hostname in a Ingress
  - port in a service or container
  - timeout or replica values
  - etc
- `var`: These are intended as environment variable in containers. These are usually in ALL_CAPS and should only be used in
  - ConfigMap
  - Kustomization configmaps

In the example below, `ENV` is given a fixed value (derived from app.env).
The other two vars `DB_URL` and `KAFKA_URL` have an "emtpy" value `{}`
and will get their value from `var.DB_URL` and `var.KAFKA_URL`
```yaml
strukt:
  Kustomization:
    main:
      configmaps:
        app-vars:
          vars:
            ENV: {{ app.env }}
            DB_URL: {}
            KAFKA_URL: {}
```
## secret
`secret`s serve a similar purpose as `var`s, except that they are meant for sensitive information
They are intended to be used in kubernetes Secret resources.

In the konfig they are specified as follows
```yaml
secret:
  DB_USR: myapp_prd_user
  DB_PSW: dekrypt:gAAA...QLEc=
  KAFKA_USR: myapp
  KAFKA_PSW: dekrypt:gAAA...dx2A=
```
Note:
- You can store both USR and PSW as secret. The username often is not really secret, but this way you can keep them together.
- The lines of encrypted items start with `dekrypt:`, so that this secrets will not be visible.

You can use these secrets as follows
```yaml
strukt:
  Secret:
    main:
      vars:
        ENV: {{ app.env }}
        DB_USR: {}
        DB_PSW: {}
        KAFKA_USR: {}
        KAFKA_PSW: {}
```
You can provide a value, but if this is left empty (with an empty set), it is fetched from the `var:` section


## inklude
One of the powerful features of `kreate` is the inklude mechanism.
This allows to inklude extra konfig files with further yaml items.

This yaml is merged into the existing with the following behavior:
- dictionaries are merged
- lists are appended
- string items are overwritten

When an inkluded yaml contains some new `inklude` items, these are appended
at the end of the `inklude:` list and be inkluded later
(Technically this is a breadth-first list and not depth-first)

This is an example of a toplevel konfig file:
```yaml, caption=demo.konf
app:
  appname: demo
  env: acc
  ...
inklude:
- shared:init.konf
```
The shared/init.konf can be inkluded by many applications and will again contain
multiple inkludes:
```yaml, caption=shared:init.konf
inklude:
- py:kreate.kube:kube-defaults.konf
- shared:{{app.env}}/shared-values-{{app.env}}.konf
- shared:{{app.env}}/shared-secrets-{{app.env}}.konf
- shared:init-templates.konf
- shared:inklude-app-files.konf
```
The above list inkludes several things:
- default values from the python (py:) kreate.kube module
- default values and secrets that are defined to be shared between all applications
- template definitions that can be used by all applications
- finally some inklude files that are defined elsewhere and are application specific. This could be a file like
```yaml, caption=shared:inklude-app-files.konf
inklude:
- optional:values-{{app.appname}}-{{app.env}}.konf
- optional:secrets-{{app.appname}}-{{app.env}}.konf
- strukts:{{app.appname}}-strukt.konf
- optional:extra-{{app.appname}}-{{app.env}}-strukt.konf
```
These contain values and secrets, specific for this application and environment.
Then it will download a generic file with strukt elements for all environments,
which optionally can be overridden/extended with some extra strukt elements
specific for this environment

## repo
Files can be inkluded from the local filesystem, but also from remote locations.
These are called repo's, and several things (like authentication) can be tuned.
The repo mechanism of repo's is already very flexible, but some details
our still subject to change.
```yaml
system:
  repo:
    templates:
      version: {{ version.shared_templates | default("v1.0") }}
      type: bitbucket-zip
      url: https://git.example.org/rest/api/latest/projects/kreate/repos/shared-templates

    shared:
      version: {{ version.shared_konfig | default("v1.0") }}
      type: bitbucket-zip
      basic_auth:
        usr_env_var: BITBUCKET_USR
        psw_env_var: BITBUCKET_PSW
      url: https://git.example.org/rest/api/latest/projects/kreate/repos/shared-konfig-{{app.env}}
```
The above example defines two repo's
- templates: This repo contains some custom templates that can be used in all applications
- shared: This repo contains files with environment specifiv values, vars, and other stuff that can be used in all applications
Note that the shared repo requires a username/password to access it.
These are provided by environment variables `BITBUCKET_USR` and `BITBUCKET_PSW`
