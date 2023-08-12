#!/bin/sh
echo setting dekryption key
export KREATE_KRYPT_KEY_DEV=C6XOvZALFPjTzWKOPV3EJFIpmmwMhXEE


echo '###########################################'
echo python3 -m kreate.kube -a tests/script/appdef.yaml -w test
python3 -m kreate.kube -a tests/script/appdef.yaml -w test

echo '###########################################'
echo ./tests/script/kreate-demo-from-script.py -w test
./tests/script/kreate-demo-from-script.py -w test

echo '###########################################'
echo ./tests/script/kreate-demo-from-konfig.py -w test
./tests/script/kreate-demo-from-konfig.py -w test
