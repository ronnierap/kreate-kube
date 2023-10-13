#!/usr/bin/env python3
"""
This test script shows that you can kreate komponents from a python script.
The komponents will still be configured by the konfig.strukture.
You can also configure them further in python.
In general it is preferred to kreate all komponents from the strukture.
"""

import kreate.kube
import kreate.kube.resource
from kreate.kube import KubeCli, KustApp


class DemoScriptApp(KustApp):
    def kreate_komponents(self) -> None:
        kreate.kube.resource.Ingress(self, "root")
        kreate.kube.resource.Ingress(self, "api")

        kreate.kube.resource.Egress(self, "db")
        kreate.kube.resource.Egress(self, "redis")
        kreate.kube.resource.Egress(self, "xyz")

        depl = kreate.kube.resource.Deployment(self)
        self.kreate_komponent("Service", "main")
        self.kreate_komponent("Service", "https")
        self.kreate_komponent("PodDisruptionBudget", "main")
        kreate.kube.Kustomization(self)
        self.kreate_komponent("Secret", "main")
        self.kreate_komponent("Secret", "secret-files")
        self.kreate_komponent("ServiceAccount")
        self.kreate_komponent("ServiceMonitor")
        self.kreate_komponent("HorizontalPodAutoscaler")
        self.kreate_komponent("MyUdpService", "main")
        self.kreate_komponent("CronJob", "main")
        self.kreate_komponent("StatefulSet", "main")
        self.kreate_patch(self.deployment.main, "HttpProbes")
        self.kreate_patch(depl, "AntiAffinity")
        # Add the next two in alphabetical order, to be predictable
        self.kreate_patch(depl, "VolumeMounts", "demo-extra-files")
        self.kreate_patch(depl, "VolumeMounts", "demo-files")
        self.kreate_patch(depl, "VolumeMounts", "demo-secret-files")
        self.kreate_patch(depl, "KubernetesAnnotations")
        self.kreate_patch(depl, "ElasticLogging")
        self.kreate_patch(depl, "EgressLabels")
        self.kreate_patch(self.statefulset.main, "KubernetesAnnotations")
        self.kreate_patch(self.statefulset.main, "ElasticLogging")
        self.aktivate_komponents()

    def tune_komponents(self) -> None:
        self.ingress.root.sticky()
        self.ingress.root.whitelist("10.20.30.40")
        self.ingress.root.basic_auth()
        self.ingress.root.label("dummy", "jan")
        pdb = self.poddisruptionbudget.main
        pdb.yaml.spec.minAvailable = 2
        pdb.label("testje", "test")


KubeCli(app_class=DemoScriptApp).run()
