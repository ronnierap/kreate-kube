from kreate.kore._kontext import Kontext
from kreate.kore._kore import KoreModule
from kreate.krypt._krypt import KryptModule
from kreate.kube._kube import KubeModule
from kreate.kube._kust import KustomizeModule
from kreate.kore._cli import Cli


def main():
    kontext: Kontext = Kontext()
    kontext.add_module(KoreModule())
    kontext.add_module(KryptModule())
    kontext.add_module(KubeModule())
    kontext.add_module(KustomizeModule())
    cli = Cli(kontext)
    cli.run()


if __name__ == "__main__":
    main()
