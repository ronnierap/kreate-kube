#!/usr/bin/env python3
import kreate
import appdef

def kreate_config(env: str) -> kreate.core.Config:
    cfg = kreate.core.Config()
    cfg._values.add_obj(appdef)
    cfg._values.add_yaml(f"tests/script/values-{env}.yaml")
    cfg.add_files(
        f"tests/script/config-demo-{env}.yaml",
        "tests/script/demo-strukt-extras.yaml",
        "tests/script/demo-strukt.yaml",
        "src/kreate/templates/default-values.yaml",
        )
    return cfg


def kreate_app(env: str) -> kreate.App:
    app = kreate.App('demo', env, config=kreate_config(env))
    app.kreate_from_config()
    return app

kreate.run_cli(kreate_app)
