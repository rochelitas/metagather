#! /bin/bash
cd $(dirname $(readlink -f "$0"))
if [ ! -d ./venv ]; then
  
fi

source ./venv/bin/initialize
python run-merge.py
