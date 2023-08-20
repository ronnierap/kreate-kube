from . import KubeKreator, KubeCli

def main():
    KubeCli(KubeKreator()).run()

if __name__=="__main__":
    main()
