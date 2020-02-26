#!/bin/bash
cd "$(dirname "$0")"
python3 setup.py install --record files.txt
# uninstall: xargs rm -rf < files.txt
