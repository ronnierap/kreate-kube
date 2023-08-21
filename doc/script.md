# Using a minimal python script
The strukture file is always needed, and usually it should be all you need.
However originally `kreate` was more script based (originally even bash scripts).
It is still possible to use a script and there might be cases where you need to finetune some things
that can only be done in Python.

This is an example how to do that

## kreate-demo.py
```
#!/usr/bin/env python3

from kreate.kore import Konfig, App
from kreate.kube import KustApp, KubeKreator

def kreate_app(konfig: Konfig) -> App:
    app = KustApp(konfig)
    app.kreate_komponents_from_strukture()
    app.aktivate()

    # Start finetuning the yaml komponents
    # Note: adding a custom label does not require python
    app.depl.main.label("custom-label","added-by-script")
    return app

KubeKreator(kreate_app).kreate_cli().run()
```
