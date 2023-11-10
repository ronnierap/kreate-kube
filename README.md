# kreate-kube
kreate kubernetes/kustomize yaml files based on templates

The purpose of the kreate-kube framework is to easily create
kubernetes resources for an application.
This is especially useful if you have many different applications
that you would like to keep as similar as possible,
while also having flexibility to tweak each application.

## Installing and running kreate-kube
### Installing
see [versions](doc/versions.md) for available versions.

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

kreate files   # kreate all files based on the `kreate*.konf` file in the current directory
kreate         # The same (files is the default command)

kreate diff    # kreate output that shows differences between the kreate and a real kubernetes cluster
kreate apply   # apply the kreated files to a kubernetes cluster
```
Note: for `diff` and `apply` your `.kube/config` should be set up correctly


By default `kreate` will look for a file `kreate*.konf` in your current directory.
It is possible to specify a different directory or file using the `--konfig` option.
If this is a directory it will look for a `kreate*.konf` file in this directory.


## Example using application structure file
Kreating resources is based on a application strukture definition file.
Usually there are ate least 3 files needed for a setup:
- `kreate*.konf`  ties all together
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
  db: {}

Ingress:
  root:
    path: /
    annotations:
      nginx.ingress.kubernetes.io/auth-realm: demo-realm
      nginx.ingress.kubernetes.io/auth-secret: demo-basic-auth
      nginx.ingress.kubernetes.io/auth-type: basic

Kustomization:
  main:
    configmaps:
      demo-vars:
        vars:
          ENV: {}
          DB_URL: {}

Secret:
  main:
    name: demo-secrets
    vars:
      DB_PSW: {}
      DB_USR: {}

SecretBasicAuth:
  basic-auth:
    users:
      - admin
      - guest

Service:
  main:
    name: demo-service
```
Note: This shows only a small subset of possibilities of kreate-kube.

As you can see not any specific values are provided in the strukture.
These values will be gotten from the `val:` section, and for
environment variables from the `var:` section, or `secret:` section.

### vals, vars and secrets
These 3 sections can be put in one file or split over multiple files.
For the above strukture it could simply be something like:
```
val:
  Ingress:
    host: demo.example.com
    service: demo-service
  Egress:
    db:
      cidr_list: 1.2.3.4/32,1.3.4.8/32
      port_list: "1521"
var:
  ENV: {{ app.env }}
  DB_URL: jdbc:oracle.example.com

secret:
  var:
    DB_USR: mark
    DB_PSW: dekrypt:....
  basic_auth:
    admin: ...
    guest: ...
```

### kreate-demo.konf
The `kreate-demo.konf` ties everything together:
- Some general values (mainly application name and enviroment)
- extra environment specific "stuff" to load
  -  values such as IP numbers and urls
  -  secrets such as usernames and passwords
- what strukture file(s) to use
In general values and secrets will be loaded from separate files, to keep the `kreate-demo.konf` file simple,
and to separate this environment specific part separated.

The file can contain several other things as well:
-  files to be mounted in a pod, such as application configuration files
-  secret_files as files, but encrypted and stored as kubernetes Secret
-  extra custom templates for resources and patches

Below is a simple but typical example.
```
app:
  appname: demo
  env: dev
  team: knights
val:
  project: kreate-kube-demo
  image_version: 2.0.2
inklude:
  - values-demo-dev.yaml
  - secrets-demo-dev.yaml
  - demo-strukture.yaml
```


## Help
this is the output of the `kreate-kube --help` command
```
$ kreate --help
usage: kreate [optional arguments] <konfig> [<subcommand>] [subcommand options]

kreates files for deploying applications on kubernetes

positional arguments:
  see subcommands

optional arguments:
  -h, --help            show this help message and exit
  --testdummy           do not dekrypt values
  -k file, --konfig file
                        konfig file or directory to use (default=KREATE_MAIN_KONFIG_PATH or .)
  -d yaml-setting, --define yaml-setting
                        add yaml (toplevel) element to konfig file
  -i path, --inklude path
                        inklude extra files before parsing main konfig
  -v, --verbose         output more details (inluding stacktrace) -vv even more
  -w, --warn            only output warnings
  -W filter, --warn-filter filter
                        set python warnings filter
  -q, --quiet           do not output any info, just essential output
  -K, --keep-secrets    do not remove secrets dirs
  --no-dotenv           do not load .env file from working dir
  --no-kreate-env       do not load kreate.env file from user home .config dir

subcommands:
  files             f   kreate all the files (default command)
  command           cmd run a predefined command from system.command
  shell             sh  run one or more shell command including pipes
  clear_repo_cache  cc  clear the repo cache
  version           vr  view the version
  view              v   view the entire konfig or subkey(s)
  dekrypt           dek
  enkrypt           enk
  build             b   output all the resources
  diff              d   diff with current existing resources
  apply             a   apply the output to kubernetes
  test              t   test output against expected-output-<app>-<env>.out file
  test_update       tu  test output against expected-output-<app>-<env>.out file
  test_diff         td  test output against expected-output-<app>-<env>.out file
  test_diff_update  tdu update expected-output-<app>-<env>.out file
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

Initially the idea was to use python scripts just like we were doing in bash.
The yaml konfiguration became so powerful, that scripting was not needed
at all, and you could specify everything in yaml (and jinja2 templates).

The new approach is to use only yaml and jinja2, even for extending the
framework with new templates and other behaviour.
