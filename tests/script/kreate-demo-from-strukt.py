#!/usr/bin/env python3
import kreate

def kreate_config(env: str) -> kreate.AppConfig:
    return kreate.AppConfig(env, "tests/script/appdef-extras.yaml")

def kreate_app(env: str) -> kreate.App:
    app = kreate.App('demo', env, config=kreate_config(env))
    app.kreate_from_config()
    return app

kreate.run_cli(kreate_app)
