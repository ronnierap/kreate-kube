import kreate.App
import kreate.Base


class Ingress(kreate.Base):
    def __init__(self,
                 app: kreate.App,
                 name="root",
                 sticky=False,
                 path="/",
                 host="TODO",
                 port=8080):
        kreate.Base.__init__(self, app, "ingress", name)
        self.sticky = sticky
        self.path = path
        self.host = host
        self.port = port

    def apply(self, app: kreate.App) -> None:
        app.kreate_file(app.name + "_" + self.name + ".yaml", self.template)

    def nginx_annon(self, name: str, val: str) -> None:
        self.annotations["nginx.ingress.kubernetes.io/" + name] = val

    def rewrite_url(self, url: str) -> None:
        self.nginx_annon("rewrite-target", url)

    def read_timeout(self, sec: int) -> None:
        self.nginx_annon("proxy-read-timeout", str(sec))

    def max_body_size(self, size: int) -> None:
        self.nginx_annon("proxy-body-size", str(size))

    def whitelist(self, whitelist: str) -> None:
        self.nginx_annon("whitelist-source-range", whitelist)

    def session_cookie_samesite(self) -> None:
        self.nginx_annon("session-cookie-samesite", "None")

    def basic_auth(self, secret : str = "basic-auth") -> None:
        self.nginx_annon("auth-type", "basic")
        self.nginx_annon("auth-secret", secret)
        self.nginx_annon("auth-realm", self.app.name + "-realm")

    def kreate(self):
        self.kreate_file(self.template)

    template = """apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ ingress.name }}
  namespace: {{ app.namespace }}
  annotations:
  {% if ingress.sticky %}
      nginx.ingress.kubernetes.io/affinity: cookie
  {% endif %}
  {% for anno, val in ingress.annotations| dictsort %}
      {{ anno }}: {{ val }}
  {% endfor %}
spec:
  rules:
    - host: {{ ingress.host }}
      http:
        paths:
          - pathType: Prefix
            path: {{ ingress.path }}
            backend:
              service:
                name: {{ app.name }}-service
                port:
                  number: {{ ingress.port }}"""
