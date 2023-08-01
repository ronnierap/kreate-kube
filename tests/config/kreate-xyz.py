#!/usr/bin/env python3
import kreate

def kreate_xyz_app(env: str):
    cfg = kreate.ConfigChain(
        f"tests/config/config-xyz-{env}.yaml",
        "tests/config/xyz-strukture.yaml",
        "src/kreate/templates/default-values.yaml",
        )
    return kreate.Strukture('xyz', env, config=cfg)


kreate.run_cli(kreate_xyz_app)
