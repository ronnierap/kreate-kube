# Using a minimal python script
The strukture file is always needed, and usually it should be all you need.
However originally `kreate` was more script based (originally even bash scripts).
It is still possible to use a script and there might be cases where you need to finetune some things
that can only be done in Python.

This is an example how to do that

## kreate-demo.py
```
#!/usr/bin/env python3

from kreate.kore import App
from kreate.kube import KubeCli


class DemoStruktCli(KubeCli):
    def _tune_app(self, app: App) -> None:
        app.kreate_komponents_from_strukture()
        app.aktivate()
        app.depl.main.label("this-is-added", "by-script")


DemoStruktCli().run()
```
