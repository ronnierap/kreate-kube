# Example application

## `kreate-<app>-<env>.konf`
When `kreate` is started it will look for a file with name `kreate*.konf` (where `*` is a wildcard).
This can be any file that starts with `kreate`, but it is recommended to add the name of
the application and the environment in the filename.
This way each file is unique and the filename indicates what will be kreated.

Below is a simple example

#### `kreate-demo-acc.konf`
```
app:
  appname: demo
  env: acc
  team: camalot
  uses:
    - db/postgres-acc.konf
    - redis/redis-aws-acc.konf
version:
  app_version: '1.2.3'
  knn_framework_version: '1.0'
inklude:
- framework/knn-framework-repo.konf
- knn-framework:init.konf
```
This file defines most things that are needed using the knn-framework.
- The application name, team and version
- The environment that it should be deployed to (`acc`)
- The (backend) system or other definitions that will be used.
- The version of the framework to use.
- Inklude where the framework repo can be found, and call the `init.konf` file of the framework

Note: be careful when specifying versions in yaml, since they might be interpreted as
floating point values, conform the YAML specification.
It is best to quote these values.


To understand in more detail what the knn-framework will do, see [example-framework](./example-framework.md).
For basic understanding, all you need to know is that it will inklude some files for you:
- `optional:default-values-demo.konf`
- `optional:values-demo-acc.konf`
- `optional:secrets-demo-acc.konf`
- `optional:demo-strukt.konf`

- The `strukt` file defines the main strukture of komponents that make up the application.
- The other files are loaded before that and define values that might be needed.
  - The `default-values` should be generic for all environments of the `demo` application.
  - The `values-demo-acc` defines specific values fot the `acc` environment (which might override `default-values`)
  - The `secrets-demo-acc` is similar as `values-demo-acc`, but makes it more clear that this can be sensitive information (and should be enkrypted)

The files are `optional:` so you may not have them all (especially default-vlaues or secrets are not always needed)

The next sections will give examples of these files

## `<app>-strukt.konf`
The strukt file defines what komponents are needed to deploy an application.
Typically for a webservice/frontend application these are:
- A Deployment (instead of a Deployment you can also define StatefulSets or CronJobs)
- A Service to loadbalance between the pods
- ConfigMaps and Secrets (optionally created by `kustomize`)
- One or more Ingress objects to access the service outside of kubernetes
- Zero or more Egress objects

Below is a typical (simple) example
#### `demo-strukt.konf`
```
inklude:
- knn-templates:helper/std-deployment.konf

strukt:
  Deployment:
    main:
      probe_path:  /some-special-path/health

  Egress:
    postgres-acc:
      cidr_list: 1.2.3.4
      port_list: 5432

  Ingress:
    all:
      path: /

  Kustomization:
    main:
      configmaps:
        demo-vars:
          vars:
            DB_URL: {}
            ENV: {{ app.env }}

  Secret:
    main:
      vars:
        DB_PSW: {}
        DB_USR: {}
```
Note that most vars (including secrets) are not defined in the strukture, since they are environments specific.
Instead an empty set `{}` as placeholder is used.
The templates for `Kustomization`, `ConfigMap` and `Secret` will get the values for either
the `var:` section or from the `secret.var` section.

Because some patterns are almost always the same, the knn-framework has a
helper that defines some of these typical things:

#### `knn-templates:helper/std-deployment.konf`
```
strukt:
  Deployment:
    main:
      vars:
      - {{app.appname}}-vars
      secret-vars:
      - {{app.appname}}-secrets
      patches:
      - AntiAffinity
      - HttpProbes
      - EgressLabels
      - KubernetesAnnotations
  PodDisruptionBudget: {}
  Service: {}
```

## `default-values-demo.konf`
This file defines some defaults that can be used for all environments
```
val:
  Deployment:
    cpu_limit:   1000m
    cpu_request: 88m
    memory_limit:   2048Mi
    memory_request: 2048Mi
    terminationGracePeriodSeconds: 120
  HttpProbes:
    startup_failureThreshold: 150
    startup_initialDelaySeconds: 30
```

## `values-demo-acc.konf`
```
var:
  DB_URL: jdbc:postgresql://postgres.example.com:5432/demodb
```

## `secrets-demo-acc.konf`
```
secret:
  var:
    DB_USR: DEMO_ACC_USR
    DB_PSW: dekrypt:...
```
