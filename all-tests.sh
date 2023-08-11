#!/bin/sh
echo setting dekryption key
export KREATE_KRYPT_KEY_DEV=C6XOvZALFPjTzWKOPV3EJFIpmmwMhXEE


echo '###########################################'
echo python3 -m kreate.kube -a tests/script/appdef.yaml -q test
python3 -m kreate.kube -a tests/script/appdef.yaml -q test

echo '###########################################'
echo ./tests/script/kreate-demo-from-script.py -q test
./tests/script/kreate-demo-from-script.py -q test

echo '###########################################'
echo ./tests/script/kreate-demo-from-konfig.py -q test
./tests/script/kreate-demo-from-konfig.py -q test
