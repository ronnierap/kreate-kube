#!/bin/sh
echo setting dekryption key
export KREATE_KRYPT_KEY_DEV=C6XOvZALFPjTzWKOPV3EJFIpmmwMhXEE


echo '###########################################'
echo python3 -m kreate.kube -a tests/demo/appdef.yaml -w test
python3 -m kreate.kube -a tests/demo/appdef.yaml -w test

echo '###########################################'
echo ./tests/demo/kreate-demo-from-script.py -a ./tests/demo -w test
./tests/demo/kreate-demo-from-script.py -a ./tests/demo -w test

echo '###########################################'
echo ./tests/demo/kreate-demo-from-strukt.py -a ./tests/demo -w test
./tests/demo/kreate-demo-from-strukt.py -a ./tests/demo  -w test
