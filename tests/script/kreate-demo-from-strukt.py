#!/usr/bin/env python3
import kreate
import appdef

def kreate_demo_app(env: str):
    cfg = kreate.core.Config()
    cfg._values.add_obj(appdef)
    cfg._values.add_yaml(f"tests/script/values-{env}.yaml")
    cfg.add_files(
        f"tests/script/config-demo-{env}.yaml",
        "tests/script/demo-strukt.yaml",
        "src/kreate/templates/default-values.yaml",
        )

    app = kreate.App('demo', env, kustomize=True, config=cfg)
    app.kreate_strukture()
    return app

kreate.run_cli(kreate_demo_app)
