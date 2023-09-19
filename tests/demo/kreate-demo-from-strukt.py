#!/usr/bin/env python3
"""
This test script shows that you can kreate komponents from strukture file.
After this you can finetune them further in python.
In general it is preferred to not use a script but use `python3 -m kreate`
"""

from kreate.kube import KubeCli, KustApp

class DemoStruktApp(KustApp):
    def tune_komponents(self) -> None:
        self.deployment.main.label("this-is-added", "by-script")


KubeCli(app_class=DemoStruktApp).run()
