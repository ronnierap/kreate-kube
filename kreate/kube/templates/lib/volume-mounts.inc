{% if my.strukture.get_path("cm-files",{}) or my.strukture.get_path("secret-files",{})%}
        volumeMounts:
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
      volumes:
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
{% endif %}
