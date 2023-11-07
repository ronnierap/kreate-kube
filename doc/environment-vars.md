# Use of environment variables

The use of kreate can be customized by several command line variables.
These can be set in several different ways:
- by setting these vars in you shell using `export KREATE_...=...`
- by setting these when calling kreate with the shell syntax before the main command `KREATE_...=... kreate ..`
- by placing them in the `.env` file in you working directory
- by placing them in the `~/.config/kreate/kreate.env` file

These methods can be combined.
If an environment var is already set, the last two methods will not override them.
The syntax of the last two files is very simple, but does have a `+=` operator to add to
existing variables.
Especially for `KREATE_OPTIONS` this can make it easy to turn certain options
on and off


## Example .env file
```
# look in . and deploy-demo-dev directories for a main kreate*.konf file
KREATE_MAIN_KONFIG_PATH=.:deploy-demo-dev

# Add a option when starting kreate
#KREATE_OPTIONS+=--define system.repo.kreate-template.version=1.2.3

# add an extra file to be inklude before the main konfig file
#KREATE_OPTIONS+=-i cwd:init-tests.konf

# You can also define your own variables
MY_DEV_DIR=/home/mark/develop/

# Disable and enable certain Python warnings
# The syntax should be mostly compatible with the python cli
#KREATE_OPTIONS+=-W default::VersionWarning
KREATE_OPTIONS+= -W ignore
#KREATE_OPTIONS+= -W default
#KREATE_OPTIONS+= -W always

# The value below are useful for debugging inklude repos, with needing
# to commit and push them each time
KREATE_REPO_USE_LOCAL_DIR=True
#KREATE_REPO_USE_LOCAL_DIR_APP_SRC=False
KREATE_REPO_LOCAL_DIR=/home/mark/develop/{my.repo_name}
KREATE_REPO_LOCAL_DIR_KREATE_TEMPLATES=/home/mark/develop/kreate-kube-templates
KREATE_REPO_LOCAL_DIR_SYSTEMS=/home/mark/develop/shared-systems
KREATE_REPO_LOCAL_DIR_VALUES=/home/mark/develop/shared-values-{app.env}
KREATE_REPO_LOCAL_DIR_SECRETS=/home/mark/develop/shared-secrets-{app.env}
KREATE_REPO_LOCAL_DIR_APP_SRC=/home/mark/develop/{app.bitbucket_project}/{app.appname}.app

# This is used with the test commands.
# it provides a string that is output when dekrypting a string
# in order to not leak secrets
KREATE_DUMMY_DEKRYPT_FORMAT=test-dummy


# This does not work, since needs to be set before running python
# export PYTHONPATH=/home/mark/develop/kreate-kube/
```

## All variables

- `KREATE_MAIN_KONFIG_PATH`: default=`.`
- `KREATE_MAIN_KONFIG_FILE`: default=`kreate*.konf`
- `KREATE_REPO_CACHE_DIR`: default=`~/.cache/kreate/repo`
- `KREATE_OPTIONS`: default=`""`
- `KREATE_TEST_EXPECTED_OUTPUT_LOCATION`: default=`cwd:tests/expected-output-{app.appname}-{app.env}.out`
- `KREATE_TEST_EXPECTED_DIFF_LOCATION`: default=`cwd:tests/expected-diff-{app.appname}-{app.env}.out`
- `KREATE_REPO_USE_LOCAL_DIR`: default=`False`
- `KREATE_REPO_USE_LOCAL_DIR_<repo_name>`: default=`KREATE_REPO_USE_LOCAL_DIR`
- `KREATE_REPO_LOCAL_DIR`: default=`..`
- `KREATE_REPO_LOCAL_DIR_<repo_name>`: default=`KREATE_REPO_LOCAL_DIR`
- `KREATE_DUMMY_DEKRYPT_FORMAT`: The default is a complicated string that should be pretty unique, without showing information
