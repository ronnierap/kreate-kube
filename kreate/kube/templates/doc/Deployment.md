# Deployment
This template klass is to kreate a kubernetes Deployment with one container.
Other containers must be added through patches


A Deployment can have several sections:
- `field:` contains values that will be retrieved using the `{{ my.field...}}` mechanism.
  Usually these are provided by values, and not "hardcoded" in the strukt,
  but for some values (e.g. image_name), this might make sense
- `annotations:` add toplevel annotations
- `labels:` add toplevel labels
- `pod:` add any yaml on pod level
- `pod.labels:` add labels to the metadata of a pod (not the Deployment). This is kept for backward compatibility but may change in future
- `container:` add any yaml on container level
- `files:` a convenient way to mount files in the container, from a ConfigMap (cm) or secret

Note: The first 3 sections are inherited from the `Resource` komponent type, and available

Note that the field section, at this moment is not required.
Fields can currently be placed at the toplevel of a Komponent strukture as well.
Before `kreate-kube` version 1.7.0 they could only be placed at the toplevel.
This might change in the future (kreate-kube 2.0).

Listed below are all the fields supported by Deployment.
A Patch will also look for fields in the target, so all the fields
of HttpProbes patch (like readiness_path) can be set in a Deployment as well.

An example is found below.
```
strukt:
  Deployment:
    main:
      field:  # Note: The field is optional, but might be required in future
        containerPort: ...
        container_name: ...
        cpu_limit: ...
        cpu_request: ...
        image_name: ...
        image_repo: ...
        image_version: ...
        memory_limit: ...
        memory_request: ...
        protocol: ...
        replicas: ...
        restartPolicy: ...
        revisionHistoryLimit: ...
        probe_path: /actuator/health  # sets all probes to the same path
    annotations:  # to be added at top level
      name: value
      ...
    labels:  # to be added at top level
      name: value
      ...
    pod: # any yaml to be added to the pod, e.g.
      labels: # This is special and will be added to metadata.labels
        lbl: value
      terminationGracePeriodSeconds: 120
      ...
    container: # any yaml to be added to the container, e.g.
       ...
    files: # files to mount from configmaps
      cm:
        app-files:  # ConfigMap name
          filename: path
          ...
      secret: # as cm but for Secrets
```
