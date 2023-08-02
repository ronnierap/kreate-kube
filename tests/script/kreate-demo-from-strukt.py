#!/usr/bin/env python3
import kreate
import appdef

def kreate_demo_app(env: str):
    cfg = kreate.core.Config()
    cfg._values.add_obj(appdef)
    cfg._values.add_yaml(f"tests/script/values-{env}.yaml")
    cfg.add_files(
        f"tests/script/config-demo-{env}.yaml",
        "tests/script/demo-strukt-extras.yaml",
        "tests/script/demo-strukt.yaml",
        "src/kreate/templates/default-values.yaml",
        )

    app = kreate.App('demo', env, kustomize=True, config=cfg)
    app.kreate_strukture()

    # TODO: the tweaks below should be possible to read from config

    # TODO: parse labels and annontations from config spec.template
    app.depl.main.add_template_label("egress-to-db", "enabled")

    # TODO: invoke special functions, or add yaml at other locations
    app.service.main.headless()

    return app

kreate.run_cli(kreate_demo_app)
