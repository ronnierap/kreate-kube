#!/bin/sh
echo '###########################################'
echo python3 -m kreate -a tests/clean/appdef.yaml -q test
python3 -m kreate -a tests/clean/appdef.yaml -q test

echo '###########################################'
echo ./tests/script/kreate-demo.py -q test
./tests/script/kreate-demo.py -q test

echo '###########################################'
echo ./tests/script/kreate-demo-from-konfig.py -q test
./tests/script/kreate-demo-from-konfig.py -q test
