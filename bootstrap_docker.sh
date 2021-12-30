#!/bin/bash

# Bootstraps env on docker.

pip3 install wheel
pip3 install -r requirements.txt
pip3 install -r tests/requirements.txt
pip3 install -e .

mkdir state

pythonz migrate
pythonz createsuperuser --noinput
