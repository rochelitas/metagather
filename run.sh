#! /bin/bash
cd $(dirname $(readlink -f "$0"))
if [ ! -d ./venv ]; then
  virtualenv --python=python3 ./venv
  (
    source ./venv/bin/initialize
    pip install -r ./required
  )
fi

source ./venv/bin/initialize
python run-merge.py
