# kreate-kube
kreate kubernetes/kustomize yaml files based on templates

The purpose of the kreate-kube framework is to easily create
kubernetes resources for an application.
This is especially useful if you have many different applications
that you would like to keep as similar as possible,
while also having flexibility to tweak each application.

## Installing and running kreate-kube
### Installing
The `kreate-kube` framework is available on PyPi.
To install it, you will need:
- `python3`  At least version 3.8 is needed.
- `venv` virtual environments in Python when you need to use different versions of the framework.
- `pip` package installer for python, to install packages

To create a virtual environment with kreate-kube in a Linux or Unix environment (like MacOs) one should:
```
python3 -m venv .venv         # create a virtual environment in the .venv directory
. .venv/bin/activate          # activate the virtual environment
python3 -m pip  kreate-kube   # install the latest version of kreate-kube
```
This will install the kreate-kube package, including a script `kreate` that can be called from the commandline.

Note: For Windows the commands might be slightly different, but `venv` and `pip`
are well documented in the Python community.

### Running
You can now call the `kreate` command line. Some examples:
```
kreate -h          # show help info
kreate version     # show the version

kreate files   # kreate all files based on the konfig.yaml in the current directory
kreate         # The same (files is the default command)

kreate diff    # kreate output that shows differences between the kreate and a real kubernetes cluster
kreate apply   # apply the kreated files to a kubernetes cluster
```
Note: for `diff` and `apply` your `.kube/config` should be set up correctly


By default `kreate` It will look for a file `konfig.yaml` in your current directory.
It is possible to specify a different directory or file using the `--konfig` option.
If this is a directory it will look for a `konfig.yaml` file in this directory.


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
      DB_PSW: {{ secret.DB_PSW | dekrypt() }}
      DB_USR: {{ secret.DB_USR }}

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
The `konfig.yaml` ties everything together:
- Some general values (mainly application name and enviroment)
- extra environment specific "stuff" to load
  -  values such as IP numbers and urls
  -  secrets such as usernames and passwords
- what strukture file(s) to use
In general values and secrets will be loaded from separate files, to keep the `konfig.yaml` file simple,
and to separate this environment specific part separated.

The file can contain several other things as well:
-  files to be mounted in a pod, such as application configuration files
-  secret_files as files, but encrypted and stored as kubernetes Secret
-  extra custom templates for resources and patches

Below is a simple but typical example.
```
{% set appname = "demo" %} # reuse the appname in rest of this file
{% set env = "acc" %}      # reuse the env in rest of this file
values:
  vars:
    appname: {{ appname }}
    env: {{ env }}
    team: knights
    project: kreate-kube-demo
    image_version: 2.0.2
  files:
    - values-{{appname}}-{{env}}.yaml
secrets:
  files:
    - secrets-{{appname}}-{{env}}.yaml

strukture_files:
  - {{appname}}-strukture.yaml
```
Note: In a future version, the value-files, secrets-files and strukture_files might use sane defaults
(as allready shown using `{{ appname }}` and `{{ env }}`), so these section might be omitted in the future

## Versions of kreate-kube
At this moment there are not many versions of kreate-kube:
- `0.1.0`  This version was incomplete and does not work when installed from Pypi
- `0.2.0`  This was the first functional version
- `0.3.0`  This is the current version, and adds many backward incompatible changes
  - use of a more flat `konfig.yaml`, with a main `app` section
  - support for default files to simplify `konfig.yaml`
  - rename of several patches to remove `Patch` suffix, and not start with a verb
  - many improvements and cleanup changes

It is expected that new versions will come out regulary:
- fixing bugs
- enhancing command line interface
- adding templates
- improving templates and default values
- improving Python API
Some of these enhancements may not be backward compatible.
While in `0.x` stage there will be only garantuee for backward compatibility
between patch versions (e.g. `0.x.1` and `0.x.2`)

After the `1.0` release a semantic versioning for backward compatibilty will be used.

In general you should specify a specific version of kreate with a `requirements.txt` file.

## Help
this is the output of the `kreate-kube --help` command
```
$ kreate-kube --help
usage: kreate-kube [optional arguments] [<subcommand>] [subcommand options]

kreates files for deploying applications on kubernetes

optional arguments:
  -h, --help            show this help message and exit
  -k KONF, --konf KONF  konfig file or directory to use (default=.)
  -v, --verbose         output more details (inluding stacktrace) -vv even more
  -w, --warn            only output warnings
  -q, --quiet           do not output any info, just essential output
  -K, --keep-secrets    do not remove secrets dirs
  -R, --skip-requires   do not check if required dependency versions are installed

subcommands:
  version           vr  view the version
  view_strukture    vs  view the application strukture
  view_defaults     vd  view the application strukture defaults
  view_values       vv  view the application values
  view_template     vt  view the template for a specific kind
  view_konfig       vk  view the application konfig file (with defaults)
  requirements      rq  view the listed requirements
  dekyaml           dy  dekrypt values in a yaml file
  dekstr            ds  dekrypt string value
  dekfile           df  dekrypt an entire file
  enkyaml           ey  enkrypt values in a yaml file
  enkfile           ef  enkrypt an entire file
  enkstr            es  enkrypt string value
  files             f   kreate all the files (default command)
  build             b   output all the resources
  diff              d   diff with current existing resources
  apply             a   apply the output to kubernetes
  test              t   test output against expected-output-<app>-<env>.out file
  testupdate        tu  update expected-output-<app>-<env>.out file
  kubeconfig        kc  kreate a kubeconfig file from a template
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
  - modular design, where a team can add team-specific templates and defaults for their set of applications
  - powerful requirements.txt/pip dependency management
