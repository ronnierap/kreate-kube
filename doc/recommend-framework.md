# Recommended framework
`kreate-kube` is meant for organisations to manage a large number of different kubernetes application deployments.

The recommended way to organize this is to use a set of repositories where shared
konfiguration and templates can be stored.

## The KNN organisation
This page will document such a setup for a hypothetical organisation called KNN,
which can be thought of as the Python reference to the [KNights who say Ni](https://en.wikipedia.org/wiki/Knights_Who_Say_%22Ni!%22).

In this organisation there are several teams which each many multiple applications.
In these examples we will concentrate on the `camalot` team, which have several application.
These examples will look at the `demo` application for the `acc` (acceptance) environment

Note: In fact the examples are based on a real world case where two teams with over 30 application
in 3 environments (`dev`, `acc` and `prd`) all managed by `kreate`

Note: This framework is an example how to set up files, and can be changed in many aspects.
Almost nothing of this framework is hard coded in `kreate-kube`,

Note: If you run the `kreate` the default is to kreate files for a certain `target`.
The default target is `kustomize`, which is used in these examples but other targets
can be supported.


## `inklude` structure
This is an example of all the files that will be inkluded by the knn framework.

The main konfig file e.g. `kreate-demo-acc.konf` will just inklude two simple file:
```
app:
  appname: demo
  env: acc
  team: camalot
  uses:
  - db/postgres-acc.konf
version:
  app_version: 4.2.1
  knn_framework_version: branch.master
inklude:
- framework/knn-framework-repo.konf
- knn-framework:init.konf
```


The first inklude will only specify the location where the knn-framework repo can be found.
The second inklude will load the init.konf from knn-framework which does the rest.

The `knn-framework:init.konf` will inklude many other files.
Simply giving `view inklude` as command (or shorter `v ink`) gives a nice overview:
```
$ kreate view inklude
==== view inklude =======
inklude:
  - framework/knn-framework-repo.konf
  - knn-framework:init.konf
  - knn-framework:init-kustomize.konf
  - knn-framework:team-camalot.konf
  - knn-framework:knn-repos.konf
  - kreate-kube-templates:kustomize/kustomize-templates.konf
  - kreate-kube-templates:kustomize/kustomize-defaults.konf
  - kreate-kube-templates:kubernetes/kubernetes-templates.konf
  - kreate-kube-templates:kubernetes/kubernetes-defaults.konf
  - knn-templates:init-knn-templates.konf
  - shared-values-acc:shared-values-acc.konf
  - shared-values-acc:shared-values-team-camalot-acc.konf
  - shared-secrets-acc:shared-secrets-acc.konf
  - shared-systems:db/postgres-acc.konf
  - optional:default-values-demo.konf
  - optional:values-demo-acc.konf
  - optional:secrets-demo-acc.konf
  - optional:demo-strukt.konf
```
First some generic files for the framework itself are inkluded:
- `init-kustomize.konf` for the `kustomize` target
- `team-camalot.konf` with specfic value for the `camalot` team
- `knn-repos.konf` with location of other repositories

Once the other repositories are known, files these from these repo's can be included as well:
- `kreate-kube-templates:`  defines many templates that are part of the `kreate-kube` framework
- `knn-templates:` defines templates specifically for the KNN organisation.
- `shared-values-acc:` defines values for the acceptance environment
- `shared-secret-acc:` is to keep (shared) secrets in a separate repo from normal values
- `shared-systems:` is similar to shared values, but with systems that an application can `use:` (e..g. `db/postgres-acc`)

Finally the values, secrets and strukture for the application are loaded.
Note that these files are marked `optional:` so you could for example not have secrets or default-values.

Note that the default-values and strukt should be kept environment unaware.
This is intended that the same strukt and default-values can be used in all environments.
This is a more advanced use case and will be documented elsewhere.
