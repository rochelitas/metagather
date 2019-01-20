#! /bin/bash
set -e
: ${PYTHON:=python3.6}

cd $(dirname $(readlink -f "$0"))
if [ ! -d ./venv ]; then
  $PYTHON -m virtualenv -p $PYTHON ./venv
  (
    source ./venv/bin/activate
    pip install -r ./required
  )
fi

source ./venv/bin/activate
python run-merge.py
