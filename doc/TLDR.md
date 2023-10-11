# TL;DR
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
- repo: repositories where (shared) konfig files and templates can be located

## app
This section is small, although you can put in anything you want.
kreate does require an appname and env in most cases
```
app:
  appname: demo
  env: prd
  team: knights
  image_version: 2.0.4
```

## strukt
This is the main section where you create komponents that will result in files that are kreated.
Komponents are identified by two strings
- kind: this is actually a template name, that often is the name of a kubernetes resource, e.g. Deployment or Ingress
- short_name: this is to have multiple instances of the same kind. Often there is only one and then main is used
Examples:
```
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
```
strukt:
  Service:
    main: {}
```
In the example above it means a Service resource file will be kreated
with default behaviour.

This example can be simplified even further when there is only one komponent.
If a kind has no sub elements it is assumed to have just one `main` element
So the example above can even be abbreviated to:
```
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
```
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
```
secret:
  DB_USR: myapp_prd_user
  DB_PSW: gAAA...QLEc=  # enkrypted
  KAFKA_USR: myapp
  KAFKA_PSW: gAAA...dx2A=  # enkrypted
```
Note:
- You can store both USR and PSW as secret. The username often is not really secret, but this way you can keep them together.
- The lines of encrypted items ends with `# enkrypted`. This is used by the `dek_lines` cli subcommand to know to dekrypt these.

You can use these secrets as follows
```
strukt:
  Secret:
    main:
      vars:
        DB_USR: {{ secret.DB_USR  }}
        DB_PSW: {{ secret.DB_PSW | dekrypt() }}
        KAFKA_USR: {{ secret.KAFKA_USR  }}
        KAFKA_PSW: {{ secret.KAFKA_PSW | dekrypt() }}
```
Note:
- You have to explicitely decrypt the passwords using a jinja2 filter called `dekrypt`.
- In theory you could use any tag instead of `secret`. This is just a best practice.

## inklude and repo
One of the powerful features of `kreate` is the inklude mechanism.
This allows to inklude extra konfig files with further yaml items.

This yaml is merged into the existing with the following behavior:
- dictionaries are merged
- lists are appended
- string items are overwritten

When an inkluded yaml contains some new `inklude` items, these are appended
at the end of the `inklude:` list and be inkluded later
(Technically this is a breadth-first list and not depth-first)

Files can be inkluded from the local filesystem, but also from remote locations.
These are called repo's, and several things (like authentication) can be tuned.
The repo mechanism of repo's is already very flexible, but some details
our still subject to change.
