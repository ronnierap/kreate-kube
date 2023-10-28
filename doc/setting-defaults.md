# Setting values and defaults

The design should make it consistent and possible to use default values
on several levels.
This is enabled by two mechanisms:
- The `my.field.<fieldname>` looks into several locations to find a value
- By inkluding several konfig files one can overwrite values from earlier konf files.

## the field mechanism
The `my.field.<fieldname>` construct looks in several places to find a value/
E.g. for the field cpu_limit of a Deployment.main it will look in:
- `strukt.Deployment.main.cpu_limit` This is mostly like hardcoding a value
- `val.Deployment.main.cpu_limit` This is a good place to set a specific value for a specific component
- `val.Deployment.cpu_limit` This is a good place to set a value for all komponents of a certain type/template. (e.g. the host for all Ingresses)
- `val.generic.cpu_limit` This is a good place for values that can be used in different types, e.g. cpu_limit for Deployment, StatefulSet or CronJob, or container_port

## using inkludes
inkluding extra konf files will overwrite existing values

As generic advise to organize your inkludes would be to have some kind of order as follows:
- inklude kreate-kube-defaults.konf
- inklude shared-values-<company>.konf
- inklude shared-values-<team>.konf
- inklude shared-values-<env>.konf
- inklude <app>-default-values.konf
- inklude values-<app>-<env>.konf
- inklude <app>-strukt.konf
- inklude extra-<app>-<env>-strukt.konf
In this manner you can override generic values with more specific values, for the team, the application or the environment


# kreate-kube-defaults
The kreate-kube-defaults.konf of `kreate-kube-templates` sets the values on easy overwritable places, thus `val.generic.<field>` or `val.<kind>.<field>`.
These are the values currently set (but may change in the future)
```
val:
  generic:
    container_name: app
    servicePort: 8080
    containerPort: 8080
    replicas: 1
    image_name: {{ app.appname }}.app
    restartPolicy: "" # if not specfied explicetly defaults to Always
    imagePullPolicy: Always
    runAsUser: 1000
    runAsGroup: 1000
    cpu_limit:   1
    cpu_request: 1
    memory_limit:   "512M"
    memory_request: "512M"

  AntiAffinity:
    selector_key: app

  CronJob:
    successfulJobsHistoryLimit: 3
    concurrencyPolicy: Allow

  Deployment:
    protocol: TCP
    revisionHistoryLimit: 1
    terminationGracePeriodSeconds: "" # Defaults in kubernetes to 30

  HorizontalPodAutoscaler:
    minReplicas: 1
    maxReplicas: 3
    cpu_averageUtilization: 70
    memory_averageUtilization: 70

  HttpProbes:
    probe_path: /actuator/info

    startup_initialDelaySeconds: 10
    startup_periodSeconds: 2
    startup_timeoutSeconds: 1
    startup_successThreshold: 1
    startup_failureThreshold: 30
    startup_scheme: HTTP
    startup_path: "" # use probe_path
    startup_port: 8080

    readiness_periodSeconds: 2
    readiness_timeoutSeconds: 1
    readiness_successThreshold: 1
    readiness_failureThreshold: 1
    readiness_scheme: HTTP
    readiness_path: "" # use probe_path
    readiness_port: 8080

    liveness_periodSeconds: 2
    liveness_timeoutSeconds: 1
    liveness_successThreshold: 1
    liveness_failureThreshold: 3
    liveness_scheme: HTTP
    liveness_path: "" # use probe_path
    liveness_port: 8080

  Ingress:
    service: {{ app.appname }}-service

  KubernetesAnnotations:
    component: webservice
    managed_by: kustomize

  PodDisruptionBudget:
    minAvailable: 1

  StatefulSet:
    protocol: TCP
    revisionHistoryLimit: 1
    terminationGracePeriodSeconds: "" # Defaults in kubernetes to 30

  SidecarContainer:
    containerPort: 8888  # different from 8080
    protocol: TCP
```
