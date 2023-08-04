import kreate

def kreate_config(env: str) -> kreate.AppConfig:
    return kreate.AppConfig(env, "tests/script/appdef-extras.yaml")

def kreate_app(env: str) -> kreate.App:
    app_cfg = kreate_config(env)
    app = kreate.App(app_cfg, env)
    app.kreate_from_config()
    return app

kreate.run_cli(kreate_app)
