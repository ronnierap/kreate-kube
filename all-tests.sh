#!/bin/sh
echo '###########################################'
echo python3 -m kreate -a tests/script/appdef.yaml -q test
python3 -m kreate -a tests/script/appdef.yaml -q test

echo '###########################################'
echo ./tests/script/kreate-demo-from-script.py -q test
./tests/script/kreate-demo-from-script.py -q test

echo '###########################################'
echo ./tests/script/kreate-demo-from-konfig.py -q test
./tests/script/kreate-demo-from-konfig.py -q test
