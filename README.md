# kreate-kube
kreate kubernetes/kustomize yaml files based on templates

The purpose of the kreate-kube framework is to easily create
kubernetes resources for an application.
This is especially useful if you have many different applications
that you would like to keep as similar as possible,
while also having flexibility to tweak each application.

More detailed information can be found in the doc subfolder:
- [summary](doc/summary.md)
- [Using Python virtual envs](doc/using-python-venv-pip.md)
- [details for making jinja templates](doc/jinja-templates.md)
- [How to set default values for your komponents](doc/settings-defaults.md)
- [History of kreate-kube](doc/history.md)


## Installing kreate-kube
see [versions](doc/versions.md) for available versions.

The `kreate-kube` framework is available on PyPi.
To install it, you will need:
- `python3`  At least version 3.8 is needed.
- `venv` virtual environments in Python when you need to use different versions of the framework.
- `pip` package installer for python, to install packages
- `kubectl` a recent version is needed. it is tested extensively with v1.28.3,
  but at lest v1.21 should be used, see [https://github.com/kubernetes-sigs/kustomize]

To create a virtual environment with kreate-kube in a Linux or Unix environment (like MacOs) one should:
```
python3 -m venv .venv                # create a virtual environment in the .venv directory
. .venv/bin/activate                 # activate the virtual environment
python3 -m pip install kreate-kube   # install the latest version of kreate-kube
```
This will install the kreate-kube package, including a script `kreate` that can be called from the commandline.

Note: For Windows the commands might be slightly different, but `venv` and `pip`
are well documented in the Python community.

An alternative way to install it, without venv, is to just type
```
pip install --user kreate-kube
```
This will install the most recent version from pypi.org, that can be used anywhere

If you want to upgrade to a newer version, use:
```
pip install --upgrade kreate-kube
```
In general you should use the newest version, since they should be backwards compatible for the yaml files
If you want to use several versions, you should use Python virtual environments.
See: https://github.com/kisst-org/kreate-kube/blob/main/doc/using-python-venv-pip.md



## Running kreate
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
It is possible to specify a different directory or file using the `--konfig` or `-k` option.
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
usage: kreate [options] [<subcommand> [param ...]]

kreates files for deploying applications on kubernetes

positional arguments:
  param                 parameters for subcommand

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         output more details (inluding stacktrace) -vv even more
  -w, --warn            only output warnings
  -q, --quiet           do not output any info, just essential output
  -W filter, --warn-filter filter
                        set python warnings filter
  -k file, --konfig file
                        konfig file or directory to use (default=KREATE_MAIN_KONFIG_PATH or .)
  -d yaml-setting, --define yaml-setting
                        add yaml (toplevel) element to konfig file
  -i path, --inklude path
                        inklude extra files before parsing main konfig
  -l, --local-repo      use local repo's (force KREATE_REPO_USE_LOCAL_DIR=True)
  -K, --keep-secrets    do not remove secrets dirs
  --no-dotenv           do not load .env file from working dir
  --no-kreate-env       do not load kreate.env file from user home .config dir
  --testdummy           do not dekrypt values

subcommands:
  files             f   kreate all the files (default command)
  clear_cache       cc  clear the repo cache
  version           vr  view the version
  view              v   view the entire konfig or subkey(s); possible other subcommand arguments: [template, warningfilters, alias]
  command           cmd run a predefined command from system.command
  shell             sh  run one or more shell command including pipes
krypt commands:
  dekrypt           dek dekrypt lines|string|file <file> (abbrevs l|s|str|f|v)
  enkrypt           enk enkrypt lines|string|file <file> (abbrevs l|s|str|f)
kube commands:
  build             b   output all the resources
  diff              d   diff with current existing resources
  apply             a   apply the output to kubernetes
test commands:
  test              t   test output against expected-output-<app>-<env>.out file
  test_update       tu  update expected-output-<app>-<env>.out file with new output
  test_diff         td  test output against expected-diff-<app>-<env>.out file
  test_diff_update  tdu update expected-diff-<app>-<env>.out file with new diff
```


## configuring kreate
When kreate is running it will first load some .env files
- `$HOME/.config/kreate/kreate.env`  This is useful for global setting for all your projects
- `./.env` in your working directory to make some tweaks

Especially the first one can be very useful to set some of the most important settings, especially some secrets.
This is an example of mine:
```
# The credentials to get to bitbucket for private repo's
GIT_PSW=...
GIT_USR=mark

# the credentials needed to automatically kreate a kubeconfig file (mostly used by Jenkins)
KUBECONFIG_API_TOKEN_ACC=kubeconfig-u-...
KUBECONFIG_API_TOKEN_DEV=kubeconfig-u-...
KUBECONFIG_API_TOKEN_PRD=kubeconfig-u-...

# The key used to enkrypt and dekrypt secrets and secret-files
KREATE_KRYPT_KEY_ACC=...
KREATE_KRYPT_KEY_DEV=...
KREATE_KRYPT_KEY_PRD=...

# Ignore certain warnings (especially about using branches)
# Better to not ignore them :)
#KREATE_OPTIONS+= -W ignore

# When comparing output with test commands, use this instead of dekrypted values
KREATE_DUMMY_DEKRYPT_FORMAT=test-dummy

# When working on the framework or templates, you do not want to push and download these
# from bitbucket all the time. Just use local directories without versioning
# Note that these can use {...} which is not jinja, but python str.format()
KREATE_REPO_USE_LOCAL_DIR=True
KREATE_REPO_LOCAL_DIR=/home/mark/kreate/{my.repo_name}

# You can also
KREATE_REPO_LOCAL_DIR_KREATE_TEMPLATES=/home/mark/kreate/kreate-kube-templates
KREATE_REPO_LOCAL_DIR_KOMPANY_TEMPLATES=/home/mark/kreate/kompany-templates
KREATE_REPO_LOCAL_DIR_SHARED_KONFIG=/home/mark/kreate/shared-konfig
```
For more explanation see: https://github.com/kisst-org/kreate-kube/blob/main/doc/environment-vars.md
