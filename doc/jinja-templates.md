# Jinja templates

Jinja templates are used for 2 different parts:
1. When loading/inkluding konfig files, these files are rendered by jinja, before the yaml is parsed
2. When generating files from komponents, these are based on jinja templates

The uses are very different, and have some specific details, especially what kind of jinja context variables are available.
There are also some common context variables and filters.

# Summary
In all templates (bot for konfig and for kreated files) there are some global variables:
- `{{ konfig }}` The konfig object. (Note that while still inkluding it is only partially filled)
- `{{ jinja_extension.<func> }}` Some functions that might be useful in templates

In konfig files you can use any part of the yaml already inkluded. Examples are:
- `{{ app.env }}`
- `{{ app.appname }``}`
- `{{ version.shared_konfig_version  | default('branch.master') }}`
There also is a special var to be used for inkluding files from the same repo:
- `{{ my_repo_name }}`

In templates for creating files for a komponent you can use the following vars:
- `{{ my... }}` point to the Komponent object
- `{{ strukt... }}` can also be referenced as `{{ my.strukture }}`
- `{{ app... }}` is a convenience shortcut to the `app:` element of the konfig
Some examples are
- `{{ my.field.cpu_limit }}`
- `{{ my.shortname }}` shortname e.g. `main` or `root` (for `Ingress.root`)
- `{{ my.name }}` full name usualy for kubernetes resource, e.g. `demo-ingress-root`
- `{{ my.var(key) }}` only for `ConfigMap`
- `{{ my.secret(key) }}` only for `Secret`
- `{{ my.user(key) }}` only for `SecretbasicAuth`
- `{{ my.target... }}` only for patches, to point to the target resource of the patch
- `{{ app.env }}` or `{{ app.team }}` or `{{ app.appname }}`
- `{{ strukt.pod.labels[lbl] }}`


# Available context vars while parsing konfig files
Basically the context contains all konfig data of previously inkluded konf files.
While new files are inkluded this grows, so for each file new (sub)variable are available.
Since you can basically add any yaml in you *.konf file there is no fixed set of vars.

Some typical examples are:
- `{{ app.env }}`  since usually this is already defined in the main (first) konf file this is always available
- `{{ app.appname }}`  idem
- `{{ version.shared_konfig_version  | default('branch.master') }}`  a field of the `version` section with the jinha `default` filter to specify the master branch
- ...

Next to this there are also two special toplevel variables added
- `my_repo_name` This is the name of the repository that this file is inkluded
- `args` This is an experimental feature to pass arguments to an inklude statement. This might be removed or renamed (to `inklude_args`) in future and is not yet used, but might be very useful.


The use of `my_repo_name`  is as follows:

Suppose you inklude a certain file from a certain repo, e.g.:
```
inklude:
- my_own_repo:init.konf
```
If this file wants to inklude another file in it's own repo, it can not know for sure
what the user named it's repo. E.g.
```
inklude:
- {{my_repo_name}}:repos/kreate-kube-templates.konf
- {{my_repo_name}}:repos/shared-konfig.konf
- {{my_repo_name}}:repos/shared-secrets.konf
```
It would work if the user named this repository `my_own_repo`, but also something else like `my_framework`

# templates for generating files from komponents
After the entire konfig has been loaded, files may be generated.
Note that many commands only load the konfig, but do not kreate files.
For example the `view`, `enkrypt` and `dekrypt` commands use the konfig, but do not generate any files.

When files are generated, each komponent kreates the files according to a template.
- a komponent is identified by it's template name, and sub/short name, e.g. `Deployment.main` or `Egress.asw-redis`
- a template is defined by it's class and it's template file. The name of the template often resemble a kubernetes resource, but this is not necessary. Templates can have arbitratry names. Some templates (e.g. patches) do not match with a kubernetes resource.
Templates are defined in `system.template`, e.g.:
```
system:
  template:
    Deployment:
      class: kreate.kube.resource.Workload
      template:  {{my_repo_name}}:kubernetes/Deployment.yaml
...
    HorizontalPodAutoscaler:
      class: kreate.kube.resource.Resource
      template:  {{my_repo_name}}:kubernetes/HorizontalPodAutoscaler.yaml
    Ingress:
      class: kreate.kube.resource.Resource
      template:  {{my_repo_name}}:kubernetes/Ingress.yaml
...
    Secret:
      class: kreate.kube.resource.Secret
      template:  {{my_repo_name}}:kubernetes/Secret.yaml
    SecretBasicAuth:
      class: kreate.kube.resource.SecretBasicAuth
      template:  {{my_repo_name}}:kubernetes/SecretBasicAuth.yaml
```
Many templates have generic classes (e.g. Resource or Patch), but sometimes more specialized
classes are used.

Depending on the template class some extra features may be available.
## The `Komponent` class.
The base class for all komponents is the `Komponent` class.
```
class Komponent:
  def __init(...):
        self.app = app
        self.kind = kind or self.__class__.__name__
        self.shortname = shortname or "main"
        self.strukture = ... # the strukture specific for this komponent
        self.field = Field(self)
        name = (
            self.strukture.get("name", None)
            or app.komponent_naming(self.kind, self.shortname)
            or self.calc_name()
        )
        self.name = name.lower()
...
    def calc_name(self):
        if self.shortname == "main":
            return f"{self.app.appname}-{self.kind}"
        return f"{self.app.appname}-{self.kind}-{self.shortname}"
```
This class knows nothing about Jinja, but does have some fields that might be used.
However every komponent inherits from this class and in templates there is a var called `my`,
so a template might refer to it's fields as `{{ my.field.... }}` or `{{ my.kind }}`

Notes about the important attributes:
- The attribute `kind` is badly named and a new attribute `template` will be added.
  kind is kubernetes specific and a template can have a different name, and is not always a kubernetes resource
- A komponent has a `shortname`, e.g. `main`,
- A komponent also has a (full) `name`. This is calculated based on naming conventions, and can be specified in the strukt using `name:`
  The default name is something like `demo-ingress-root`, for the `Ingress.root` komponent of the `demo` application.
  For the `main` shortname, often a shorter convention is used.
- The `field` is a way to search for values. This is described in: [setting-defaults.md](setting-defaults.md)

## The JinjaKomponent and JinyamlKomponent
The JinjaKomponent inherits from Komponent and does not at very relevant fields for template designers.
It does add the important capability to kreate files based on Jinja templates.
It might be merged into the Komponent class, since kreating files is the base functionality of a Komponent.
However it could be imaginable that a subclass of a Komponent uses a different mechanism to kreate a file.

The JinjaKomponent does create a jinja context with some vars:
```
    def _template_vars(self):
        return {
            "strukt": self.strukture,
            "app": self.app.konfig.get_path("app", {}),
            "my": self,
        }
```
The `my` field points to the komponent class and basically makes everythin reachable.
The other two fields are mostly for convenience since they could be references as:
- `{{strukt}}` can also be referenced as `{{ my.strukture }}`
- `{{app.env}}` can also be referenced as `{{ self.app.konfig.get_path("app.env") }}`, or more simple `{{ konfig.get_path("app.env") }}`
  (see the global `konfig` var described below). This convenience is mostly since app elements like `env` and `appname` are used in many places.

Note that the `app` object is a Python object while there is also an `app` field in the config.
The `app` object of the `App` class might be renamed in the future (maybe to `Kontainer` since it is just a container of komponents)


## The JinyamlKomponent
The JinyamlKomponent inherits from the JinjaKomponent and is intended to contain YAML.
It has a specific field for this called `yaml` that can be referenced.
Note that this is the yaml **after** the entire template has been rendered and parsed as yaml.
It does not make sense to reference this field in your template, since it is not filled yet.

It does have some specific functionality to change this yaml after the template is rendered.
- if a komponent has a "toplevel" element call `add`, this can add elements at specific paths
- if a komponent has a "toplevel" element call `remove`, this can remove elements at specific paths
These capabilty to alter the generated yaml can be very powerful if you want to added some
yaml code that is not available in a template.

An example could be a Service that needs an extra field added to it's `spec`:
```
strukt:
  Service:
    main:
      add:
        spec:
          clusterIP: None
```
For a more deeply nested komponent, you can specify deeper paths, e.g.
```
strukt:
  StatefulSet:
    main:
      add:
        spec.template:
          serviceName: some-service-name
          some-other-field: dummy
        spec.template.metadata.labels:
          label1: value
          label2: value
```

## Other JinyamlKomponent sub classes
There are several subclasses Of JinyamlKomponent that might add some extra capabilities:
- Resource: base class for all kubernetes resources. Most resource can use this class, but some sub classes provide more
  -



# Common context variables and filters
Both templates use the same jinja enviroment, and thus share some properties.
The following globals are defined and available in each template:
```
    self.env.globals["konfig"] = konfig
    self.env.globals["jinja_extension"] = {
        "getenv": os.getenv,
        "sorted": sorted,
        "error": error,
        "warning": warnings.warn,
        "logger": logger,
    }
```
Basically the `konfig` variable points to the konfig python object.
It especially can be used to query specific paths with `get_path`, e.g.
```
  namespace: {{ konfig.get_path("app.namespace", app.appname + "-" + app.env) }}
```
It is a global variable so always points to the same konfig object (that slowly grows while inkluding more files)
It is a Python object with several attributes but in general this should not be (ab)used, and in future
these attributes mught be removed or shielded

The other global variable is `jinja_extension`.
This contain several Python functions that might be useful, although most are not used (yet).

There are also 3 filters available for all templates:
```
    self.add_jinja_filter("b64encode", b64encode)
    self.add_jinja_filter("handle_empty_str", handle_empty_str)
    self.add_jinja_filter("yaml", self.yaml_filter)
```

The first two are currently used for secrets:
```
  {% for key in strukt.get("vars", []) %}
    {{key}}: {{ my.secret(key) | b64encode | handle_empty_str }}
  {% endfor %}handle_empty_str
```
Secrets are stored as base64 encoded values. If this result in an empty string it is converted to the literal string `""`
using this function:
```
def handle_empty_str(value: str) -> str:
    if value == "":
        return '""'
    return value
```
It is not sure if this is really needed for correct yaml generation.

The `yaml` filter is used in very special addition.
Suppose you define:
```
strukt:
  Deployment:
    main:
      container:
        some-custom:
          - yaml
          - python
        or:
          other: fields
          and: stuff
```
The intention is to add all that yaml under the container tag to a Deployment container definition
(which is located at `spec.template.spec.containers[0]`)
```
apiVersion: apps/v1
kind: Deployment
...
spec:
  template:
    spec:
      containers:
      - name: app    # first container
        {% for item in strukt.get("container",{}).keys()  %}
        {{ item }}: {{ strukt.container[item] | yaml(indent="          ") }}
        {% endfor %}
```
The for loop with the yaml filter will add al those items at the right indent level (either specified by spaces or an integer).
The result should look like:
```
spec:
  template:
    spec:
      containers:
      - name: app    # first container
        some-custom:
          - yaml
          - python
        or:
          other: fields
          and: stuff
```
The intention of this construct is to be able to add any flexible yaml data at specific location.
There are a few places where this is currently used:
- `pod` level for Deployments, StatefulSets and CronJobs
- `container` level for Deployments, StatefulSets and CronJobs
- `job` level for CronJobs

Note that the indet parameter will not work if the template code is reformatted to a different indent.
