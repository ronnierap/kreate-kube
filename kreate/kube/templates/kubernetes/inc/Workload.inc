apiVersion: apps/v1
kind: {{ kind }}
metadata:
  name: {{ my.name }}
spec:
  replicas: {{ my.field.replicas }}
  revisionHistoryLimit: {{ my.field.revisionHistoryLimit }}
  selector:
    matchLabels:
      {{ match_label }}: {{ my.name }}
  template:
    metadata:
      name: {{ my.name }}
      labels:
        {{ match_label }}: {{ my.name }}
        # add extra labels from pod.labels
        {% for lbl in my.strukture._get_path("pod.labels",{}).keys() | sort %}
        {{ lbl }}: {{ my.strukture.pod.labels[lbl] }}
        {% endfor %}
      # add all remaining pod.items, except for the labels
      {% for item in my.strukture.get("pod",{}).keys() | sort %}
      {% if item != "labels" %}
      {{ item }}: {{ my.strukture.pod[item] | yaml(indent="        ") }}
      {% endif %}
      {% endfor %}
    spec:
      restartPolicy: {{ my.field.restartPolicy }}
      {{ my.optional("serviceAccount") }}
      {{ my.optional("serviceAccountName") }}
      {{ my.optional("serviceName") }}
      {{ my.optional("terminationGracePeriodSeconds") }}

      containers:
      - name: {{ my.field.container_name }}
        image: {{ my.field.image_repo }}/{{ my.field.image_name }}:{{ my.field.image_version }}
        {{ my.optional("imagePullPolicy") }}
        # add all container.items
        {% for item in my.strukture.get("container",{}).keys() | sort %}
        {{ item }}: {{ my.strukture.container[item] | yaml(indent="          ") }}
        {% endfor %}
        env:
{% for var in my.strukture.get("env",{}) | sort %}
        - name: {{ var }}
          value: {{ my.strukture.get("env."+var,{}) or konfig.var[var] }}
{% endfor %}
        envFrom:
{% for secr in my.strukture.get("secret-vars",[]) %}
        - secretRef:
            name: {{ secr }}
{% endfor %}
{% for cm in my.strukture.get("vars",[]) %}
        - configMapRef:
            name: {{ cm }}
{% endfor %}
        securityContext:
          runAsNonRoot: {{ my.field.runAsNonRoot }}
          {{ my.optional("runAsUser") }}
          {{ my.optional("runAsGroup") }}
        ports:
        - containerPort: {{ my.field.containerPort }}
          protocol: {{ my.field.protocol }}
        resources:
          limits:
            cpu: {{ my.field.cpu_limit }}
            memory: {{ my.field.memory_limit }}
          requests:
            cpu: {{ my.field.cpu_request }}
            memory: {{ my.field.memory_request }}
{% if my.strukture.get_path("files",{}) or my.strukture.get_path("cm-files",{}) or my.strukture.get_path("secret-files",{})%}
        volumeMounts:
############################################################
# old syntax: files.cm, and files.secret, will be deprecated in 2.0
{% for cm in my.strukture.get("files.cm", {}).keys() | sort %}
{% for filename in my.strukture.get("files.cm."+cm, {}).keys() | sort %}
         - mountPath: {{ my.strukture.get("files.cm."+cm)[filename] }}
           name: {{ cm }}
           subPath: {{ filename }}
{% endfor %}
{% endfor %}
{% for secr in my.strukture.get("files.secret", {}).keys() | sort %}
{% for filename in my.strukture.get("files.secret."+secr, {}).keys() | sort %}
         - mountPath: {{ my.strukture.get("files.secret."+secr)[filename] }}
           name: {{ secr }}
           subPath: {{ filename }}
{% endfor %}
{% endfor %}
#############################################################
# new syntax: cm-files, and secret-files, will be preferred in >=1.8.1
{% for cm in my.strukture.get("cm-files", {}).keys() | sort %}
{% for filename in my.strukture.get("cm-files")[cm].keys() | sort %}
         - mountPath: {{ my.strukture.get("cm-files")[cm][filename] }}
           name: {{ cm }}
           subPath: {{ filename }}
{% endfor %}
{% endfor %}
{% for secr in my.strukture.get("secret-files", {}).keys() | sort %}
{% for filename in my.strukture.get("secret-files")[secr].keys() | sort %}
         - mountPath: {{ my.strukture.get("secret-files")[secr][filename] }}
           name: {{ secr }}
           subPath: {{ filename }}
{% endfor %}
{% endfor %}
#############################################################
      volumes:
#############################################################
# old syntax
{% for cm in my.strukture.get_path("files.cm",{}).keys() | sort %}
      - name: {{ cm }}  # use the configmap name as volume name
        configMap:
          name: {{ cm }}
{% endfor %}
{% for secr in my.strukture.get_path("files.secret",{}).keys() | sort %}
      - name: {{ secr }} # use the secret name as volume name
        secret:
          secretName: {{ secr }}
{% endfor %}
#############################################################
# new syntax
{% for cm in my.strukture.get_path("cm-files",{}).keys() | sort %}
      - name: {{ cm }}  # use the configmap name as volume name
        configMap:
          name: {{ cm }}
{% endfor %}
{% for secr in my.strukture.get_path("secret-files",{}).keys() | sort %}
      - name: {{ secr }} # use the secret name as volume name
        secret:
          secretName: {{ secr }}
{% endfor %}
#############################################################

{% endif %}
