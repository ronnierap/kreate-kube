#!/bin/sh
echo setting dekryption key
export KREATE_KRYPT_KEY_DEV=C6XOvZALFPjTzWKOPV3EJFIpmmwMhXEEqtMAG26W7_c=


echo '###########################################'
echo python3 -m kreate -a tests/script/appdef.yaml -q test
python3 -m kreate -a tests/script/appdef.yaml -q test

echo '###########################################'
echo ./tests/script/kreate-demo-from-script.py -q test
./tests/script/kreate-demo-from-script.py -q test

echo '###########################################'
echo ./tests/script/kreate-demo-from-konfig.py -q test
./tests/script/kreate-demo-from-konfig.py -q test
