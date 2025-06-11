#!/bin/bash
set -euo pipefail

if [ -f airbase.zip ]; then
    mv airbase.zip airbase.zip.bak
else
    echo "Error: airbase.zip not found. Exiting."
    exit 1
fi

unzip airbase.zip.bak -d airbase-tmp > unzip.log 2>&1
cp patch/venv-activate airbase-tmp/venv/bin/activate
cp patch/airbase.sh airbase-tmp/airbase.sh

pip install --platform manylinux2014_x86_64 --target=./airbase-tmp/venv/lib/python3.11/site-packages/ --implementation cp --python-version 3.11 --only-binary=:all: --upgrade pydantic==2.11.5

bash -c "cd airbase-tmp && zip -r ../airbase.zip *" > zip.log 2>&1

rm -rf airbase-tmp
