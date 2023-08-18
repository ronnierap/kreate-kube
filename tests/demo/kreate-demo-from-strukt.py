#!/usr/bin/env python3
"""
This test script shows that you can kreate komponents from strukture file.
After this you can finetune them further in python.
In general it is preferred to not use a script but use `python3 -m kreate`
"""

from kreate.kore import App
from kreate.kube import KubeKreator, KubeCli


class DemoStruktKreator(KubeKreator):
    def tune_app(self, app: App) -> None:
        app.kreate_komponents_from_strukture()
        app.aktivate()
        app.depl.main.label("this-is-added","by-script")

KubeCli(DemoStruktKreator()).run()
