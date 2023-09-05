#!/bin/sh
echo setting dekryption key for testing
export KREATE_KRYPT_KEY_DEV=C6XOvZALFPjTzWKOPV3EJFIpmmwMhXEE


echo '###########################################'
echo python3 -m kreate.kube --konf tests/demo/konfig.yaml -w -R test
python3 -m kreate.kube --konf tests/demo/konfig.yaml -w -R test

echo '###########################################'
echo ./tests/demo/kreate-demo-from-script.py --konf ./tests/demo -w -R test
./tests/demo/kreate-demo-from-script.py --konf ./tests/demo -w -R test

echo '###########################################'
echo ./tests/demo/kreate-demo-from-strukt.py --konf ./tests/demo -w -R test
./tests/demo/kreate-demo-from-strukt.py --konf ./tests/demo  -w -R test
