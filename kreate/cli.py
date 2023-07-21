import argparse
import os

def cli(func):
    parser = argparse.ArgumentParser()
    cmds=["a", "apply", "d", "diff", "files"]
    help="the command to be executed, e.g. apply or diff"
    parser.add_argument("-b", "--build",  action='store_true', help="build with kustomize")
    parser.add_argument("-d", "--diff",   action='store_true', help="diff with kubernetes")
    parser.add_argument("-a", "--apply", action='store_true', help="apply to kubernetes")
    args=parser.parse_args()

    func()
    if args.build:
        print()
        os.system("kustomize build build/demo-dev")
