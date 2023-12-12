{% if my.strukture.get_path("files",{}) %}
############################################################
# old syntax: files.cm, and files.secret, will be deprecated in 2.0
        volumeMounts:
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
      volumes:
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
{% endif %}
