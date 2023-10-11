# git/pipeline choices
This page is written for a situation where we want to deploy from a CI/CD pipeline mechanism.
It has been based on experiences with Jenkins, but could be used from other CI/CD tools
that are triggered by git repositories

We have several choices where to store the kreate konfig files for a specific application `<app>`.
In this case we assume that the application source code is in a git repository called `<app>.app`.

Possibilites
- `<app>.app` repository together with the application source code
- `deploy-<app>` repository for all environments
- `deploy-<app>-<env>` repository for all environments


## `<app>.app` repository together with the (java) source code
This git repository contains the application source code, including a Dockerfile to build the image.
This source code can be anything like java, html, javascript, etc.

To store the kreate konfig here seems like a clean solution, since you do not need extra git repositories
There is only 1 repository with both application source and deployment konfig.
There is a central `<app>-strukt.konf` file that can be used by all environments.
We some good guidelines this might help that each environment uses the strukt file appropriate for the
docker image in that version

The git repo layout would be something as follows (omitting all application source code)
### `<app>.app` repo:
```
- src:             source code needed to build the application*
- docker:          directory with information to build the docker image
  - Dockerfile
  - Jenkinsfile-docker
  - ...
- kreate:          all information needed to run kreate for all environments
  - framework/
    - Jenkinsfile-acc
    - Jenkinsfile-prd
    - init-framework-1.0.konf
  - <app>-strukt.konf
  - acc/
    - deploy-<app>-acc.konf
    - values-<app>-acc.konf
    - secrets-<app>-acc.konf
  - prd/
    - deploy-<app>-prd.konf
    - values-<app>-prd.konf
    - secrets-<app>-prd.konf
```

The difficulty with this approach might be
- you need branches to signal when to deploy to an environment
- the source code and deployment configuration get mixed

You need a very strict branching strategy workflow for acc and prd:
- tag a commit, e.g. 1.3 on master branch
  - make sure the image_version is set to 1.3rc2
  - do not put tag on feature branch!!!
  - build image from that tag
- merge from that tag into deploy-acc
  - this might automatically trigger Jenkinsfile-acc
  - alternatively we start Jenkins by hand
- fix kubernetes problems for 1.3 on deploy-acc branch
- fix environment changes on for 1.3 deploy-acc branch (e.g. oracle v19 upgrade)
- when a new version 1.4 is built and needs to go to acc
  - merge deploy-acc into master (to get any changes that were needed)
  - this might also be done regulary (since bugs in `<app>-strukt.konf` might be relevant for prd)
Notes:
- same procedure for prd, and possibly dev
- deploy to dev may also been done automatically as part of the image build pipeline


## `deploy-<app>` repository for all environments
### `<app>.app` repo:
In this case we might still put some kreate konfig in the app repository
This will only be the generic konfig that should be identical for all environments
This can be inkluded from other konfig's
```
- kreate/
  - <app>-strukt.konf
```

### `deploy-<app>` repo:
Most of the konfig we be in a separate git repository
```
- framework/
  - Jenkinsfile-acc
  - Jenkinsfile-prd
  - init-framework-1.0.konf
- acc/
  - deploy-<app>-acc.konf
  - values-<app>-acc.konf
  - secrets-<app>-acc.konf
- prd/
  - deploy-<app>-prd.konf
  - values-<app>-prd.konf
  - secrets-<app>-prd.konf
  -
```

## `deploy-<app>-<env>` repository for all environments
### `<app>.app` repo:
```
- kreate/
  - <app>-strukt.konf
```
### `deploy-<app>-acc` repo:
```
- framework/
  - Jenkinsfile-acc
  - init-framework-1.0.konf
- deploy-<app>-acc.konf
- values-<app>-acc.konf
- secrets-<app>-acc.konf
- <app>-strukt.konf *optional or from `<app>.app:kreate/<app>-strukt.konf`*
```
