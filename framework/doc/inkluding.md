# Inkluding other konfig files
The famework used for kompany makes extensive use of inkluding separate files
from several repositories

loading main konfig from deploy-demoapp-acc/kreate-demoapp-acc.konf
- kreate-demoapp-acc.konf
  - ../framework/init-framework-1.0.konf
     - ../framework/kreate-framework-repo.konf
       - kreate-framework:init.konf
         - kreate-framework:repo.konf
         - kreate-templates:init-kreate-kube-templates.konf
         - kreate-templates:kreate-kube-defaults.konf
         - kreate-framework:naming-kreate-kube-templates.konf
         - kompany-templates:init-kompany-templates.konf
         - optional:kreate-framework:shared-global-values.konf
         - optional:kreate-framework:shared-team-knights-global-values.konf
         - values:init-acc.konf
         - values:shared-values-acc.konf
         - values:shared-team-knights-values-acc.konf
         - **appended from app.values**
         - values:shared-konfig:sys/redis/aws-redis-acc.konf
         - *app:docker/demoapp-default-values.konf* (added by demoapp main konfig)
         - optional:../app/demoapp-default-values.konf
         - optional:values-demoapp-acc.konf
         - optional:secrets-demoapp-acc.konf
         - **appended from app.strukt**
         - *app:docker/demoapp-strukt.konf* (added by demoapp main konfig)
         - kompany-templates:helper/std-app-strukt.konf
         - optional:../app/demoapp-strukt.konf
         - optional:extra-demoapp-acc-strukt.konf
