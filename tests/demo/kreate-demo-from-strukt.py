#!/usr/bin/env python3
"""
This test script shows that you can kreate komponents from strukture file.
After this you can finetune them further in python.
In general it is preferred to not use a script but use `python3 -m kreate`
"""

from kreate.kore import App
from kreate.kube import  KubeKreator

def tune_app(app: App) -> None:
    app.depl.main.label("this-is-added","by-script")


KubeKreator(tune_app).kreate_cli().run()
