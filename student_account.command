#!/bin/bash

export TERM=xterm-256color

clear

cd "$(dirname "$0")" 

if [ ! -d "libs" ]; then
    mkdir libs
fi

export PYTHONPATH=libs

cd scripts
python3 install_requirements.py

if [ $? -ne 0 ]; then
    echo "Нажмите любую клавишу для выхода..."
    read -n 1 -s
    exit $?
fi

cd ..
python3 -m src.main
