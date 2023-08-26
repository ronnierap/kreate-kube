#!/usr/bin/env python3
"""
This test script shows that you can kreate komponents from strukture file.
After this you can finetune them further in python.
In general it is preferred to not use a script but use `python3 -m kreate`
"""

from kreate.kube import KubeCli


class DemoStruktCli(KubeCli):
    def _tune_app(self) -> None:
        self._app.kreate_komponents_from_strukture()
        self._app.aktivate()
        self._app.depl.main.label("this-is-added", "by-script")


DemoStruktCli().run()
