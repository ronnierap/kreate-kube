# Ingress
This template klass represent a kubernetes Ingress

A simple example is
```
strukt
  Ingress:
    root:
      path: /
    api:
      path: /api
      feature:
        - basic-auth
    web:
      path: '/web'
      feature:
        - sticky
```

A more complex example is
```
strukt
  Ingress:
    api:
      path: /api(/|$)(.*)
      host: {{ val.ingress.api_host }}
      nginx_snippets:
        - proxy_set_header X-Forwarded-Path "/api";
        - proxy_set_header X-sso-hostname "api.example.com";
        - proxy_set_header X-app-path "/api";
      annotations:
        nginx.ingress.kubernetes.io/proxy-body-size: 50M
        nginx.ingress.kubernetes.io/session-cookie-samesite: None
        nginx.ingress.kubernetes.io/rewrite-target: /$2
    web:
      path: '/web'
      feature:
        - sticky
        - basic-auth
      annotations:
        # This is the same as sticky
        nginx.ingress.kubernetes.io/affinity: cookie

```
