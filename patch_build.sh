#!/bin/bash

mv airbase.zip airbase.zip.bak

unzip airbase.zip.bak -d airbase-tmp > unzip.log
cp patch/venv-activate airbase-tmp/venv/bin/activate
cp patch/airbase.sh airbase-tmp/airbase.sh

pip install --platform manylinux2014_x86_64 --target=./airbase-tmp/venv/lib/python3.11/site-packages/ --implementation cp --python-version 3.11 --only-binary=:all: --upgrade pydantic==2.11.5

bash -c "cd airbase-tmp && zip -r ../airbase.zip *" > zip.log

rm -rf airbase-tmp
