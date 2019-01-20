#! /bin/bash
set -e

cd $(dirname $(readlink -f "$0"))
if [ ! -d ./venv ]; then
  virtualenv --python=python3 ./venv
  (
    source ./venv/bin/activate
    pip install -r ./required
  )
fi

source ./venv/bin/activate
python run-merge.py
