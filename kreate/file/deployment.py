
def deployment(app, env):
    template = """apiVersion: apps/v1
kind: {{ app.kind }}
metadata:
  name: {{ app.name }}
spec:
  replicas: {{ app.replicas }}
  revisionHistoryLimit: 1
  selector:
    matchLabels:
      app: {{ app.name }}
  template:
    metadata:
      name: {{ app.name }}
      labels:
{% for lbl, val in app.labels|dictsort %}
        {{ lbl }}: {{ val }}
{% endfor %}
      annotations:
        app.kubernetes.io/name: {{ app.name }}
        app.kubernetes.io/version: "{{ app.container[0].image_version }}"
        app.kubernetes.io/component: webservice
        app.kubernetes.io/part-of: {{ env.project }}
        app.kubernetes.io/managed-by: kustomize
        co.elastic.logs/enabled: "true"
        co.elastic.logs/exclude_lines: DEBUG
    spec:
      #restartPolicy: Never
      containers:
{% for cont in app.container %}
      - name: {{ cont.name }}
        image: {{ cont.image_name }}:{{ cont.image_version }}
        imagePullPolicy: Always
        envFrom:
        - secretRef:
            name: ${SECRETS_NAME:-${APP}-secrets}
        - configMapRef:
            name: ${APP}-vars
        ports:
        - containerPort: {{ cont.port }}
          protocol: TCP
        resources:
          limits:
            cpu: {{ cont.cpu_limit }}
            memory: {{ cont.mem_limit }}
          requests:
            cpu: {{ cont.cpu_request }}
            memory: {{ cont.mem_request }}
{% endfor %}
"""
    app.kreate_file(app.name+"_deploy.yaml", template)
