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
    # - parse labels and annontations from config for all resources
    # - apply patches for resources

    kreate.HttpProbesPatch(app.depl.main)
    kreate.AntiAffinityPatch(app.depl.main)

    app.pdb.main.add_label("testje","test")
    return app

kreate.run_cli(kreate_demo_app)
