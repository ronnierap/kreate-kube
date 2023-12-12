import logging
from ..kore import App, Cli
from ..kore._core import pprint_map
from .resource import Resource


logger = logging.getLogger(__name__)

kinds = {
    "Deployment": "spec.template.spec.containers",
    "StatefulSet": "spec.template.spec.containers",
    "CronJob": "spec.jobTemplate.spec.template.spec.containers",
}

def vardiff(cli: Cli) -> None:
    """vardiff with current existing resources"""
    app = cli.kreate_files()
    app.aktivate_komponents() # render the yaml
    old_names = {}
    for komp in app.komponents:
        if isinstance(komp, Resource) and komp.kind in kinds.keys():
            find_old_names(cli, komp, old_names)
    logger.info(f"found {old_names}")
    logger.info("dumping ConfigMaps")
    paths = dump_helper(cli, app, kind_filter="ConfigMap", name_mapper=old_names)
    for path in paths: #cm, old_name in old_names.items():
        #logger.info(f"diffing {name}.{old_name}")
        print(cli.run_command(app, "diff-file", success_codes=(0,1), file=path))
        #diff_config_map(cli, cm, old_name)

def find_old_names(cli: Cli, res: Resource, old_names: dict):
    cms_names = get_used_config_maps(res)
    logger.info(f"retrieving resource {res.kind}.{res.name}")
    text = cli.run_command(res.app, "getyaml",
        resource_type=res.kind, resource_name=res.name
    )
    for line in text.splitlines():
        for cm_name in cms_names:
            if line.strip().startswith(f"name: {cm_name}-"):
                old_name = line.strip()[6:]
                old_names[cm_name] = old_name


def get_used_config_maps(komp: Resource) -> list:
    result = set()
    for container in komp.yaml.get_path(kinds[komp.kind]):
        for env in container.get("envFrom"):
            if "configMapRef" in env:
                result.add(env.get("configMapRef").get("name"))
    return result

def diff_config_map(cli: Cli, name: str, old_name: str) -> list:
    logger.info(f"diffing {name}.{old_name}")
    #cli.run_command("diff-file", file=)

    #build_result = cli.run_command(komp.app, "build")
    #documents = app.konfig.jinyaml.yaml_parser.load_all(build_result)

def dump(cli: Cli, kind_filter: str = None, name_mapper: dict = None) -> None:
    app = cli.kreate_files()
    dump_helper(cli, app)


def dump_helper(cli: Cli, app: App,  kind_filter: str = None, name_mapper: dict = None) -> None:
    """dump `kustomize build` output to individual files per resource"""
    dumped_files = []
    build_result = cli.run_command(app, "build")
    documents = app.konfig.jinyaml.yaml_parser.load_all(build_result)
    dumpdir = app.target_path / "dump"
    dumpdir.mkdir(parents=True, exist_ok=True)
    for doc in documents:
        kind = doc.get("kind")
        if kind_filter and kind != kind_filter:
            continue
        name = doc.get("metadata").get("name")
        if name_mapper:
            if len(name) > 11:
                trunc_name = name[:-11]
                if trunc_name not in name_mapper:
                    logger.warning(f"Could not find {trunc_name} in mapper list, skipping...")
                    continue
                old_name = name_mapper[trunc_name]
                logger.info(f"changing name from {name} to {old_name}")
                doc.get("metadata")["name"] = old_name
                name = old_name
        if len(cli.params) > 0:
            pattern = cli.params[0]
            if not pattern in kind + name:
                continue
        path = dumpdir / f'{kind}.{name}'
        logger.info(f"dumping to {path}")
        dumped_files.append(path)
        # TODO: not using dump, because some value might need quotes?
        #app.konfig.jinyaml.yaml_parser.dump(doc, path)
        with open(path, "w") as f:
            pprint_map(doc, file=f, use_quotes=True)
    return dumped_files
