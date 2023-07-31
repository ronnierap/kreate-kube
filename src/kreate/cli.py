import argparse
import os

def do_files(kreate_files):
    kreate_files()

def do_out(kreate_files):
    app=kreate_files()
    cmd = f"kustomize build {app.target_dir}"
    print(cmd)
    os.system(cmd)

def do_diff(kreate_files):
    app=kreate_files()
    cmd = f"kustomize build {app.target_dir} | kubectl diff -f - "
    print(cmd)
    os.system(cmd)

def do_apply(kreate_files):
    app=kreate_files()
    cmd = f"kustomize build {app.target_dir} | kubectl apply --dry-run -f - "
    print(cmd)
    os.system(cmd)

def do_test(kreate_files):
    app=kreate_files()
    cmd = f"kustomize build {app.target_dir} | diff - {app.script_dir}/test.out"
    print(cmd)
    os.system(cmd)



def cli(kreate_files):
    parser = argparse.ArgumentParser()
    cmds=["a", "apply", "d", "diff", "files"]
    help="the command to be executed, e.g. apply or diff"
    subparsers = parser.add_subparsers(help="subcommand", description="valid subcommands", title="subcmd")
    #parser.add_subparsers(title="command", help="subcommand")
    files_cmd = subparsers.add_parser("files", help="kreate all the files (default command)", aliases=["f"])
    out_cmd = subparsers.add_parser("out", help="output all the resources", aliases=["o", "b",  "build"])
    apply_cmd = subparsers.add_parser("apply", help="apply the output to kubernetes", aliases=["a"])
    diff_cmd = subparsers.add_parser("diff", help="diff with current existing resources", aliases=["d"])
    test_cmd = subparsers.add_parser("test", help="test output against test.out file", aliases=["t"])
    files_cmd.set_defaults(func=do_files)
    out_cmd.set_defaults(func=do_out)
    diff_cmd.set_defaults(func=do_diff)
    apply_cmd.set_defaults(func=do_apply)
    test_cmd.set_defaults(func=do_test)
    # from https://stackoverflow.com/questions/6365601/default-sub-command-or-handling-no-sub-command-with-argparse
    parser.set_defaults(func=do_files) # TODO: better way to set default command?

    args = parser.parse_args()
    args.func(kreate_files)
