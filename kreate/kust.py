import kreate


class Kustomization(kreate.Base):
    def __init__(self, app: kreate.App):
        kreate.Base.__init__(self, app, "Kustomize")
        self.name = "kustomization"
        self.resources = []
        self.patches = []
        self.vars = {}

    def add(self, comp: kreate.Base):
        self.resources.append(comp)
        return comp # return to allow changing a freshly create component

    def patch(self, comp: kreate.Base):
        self.patches.append(comp)
        return comp # return to allow changing a freshly create component


    def kreate(self, env: kreate.Environment):
        for rsrc in self.resources:
          rsrc.kreate(env)
        self.kreate_file(env, self.template)

    template = """apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
{% for rsrc in kustomize.resources %}
- {{ rsrc.name }}.yaml
{% endfor %}

namespace: {{ env.namespace }}

patches:
{% for patch in kustomize.patches %}
- {{ patch.name }}.yaml
{% endfor %}

configMapGenerator:
- name: {{ app.name }}-vars
  options:
    labels:
      config-map: {{ app.name }}-vars
  literals:
  {% for vars in kustomize.vars %}
  - {{ patch.name }}.yaml
  {% endfor %}"""
