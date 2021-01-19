#!/bin/bash

# Bootstraps a local development environment.
#
# Run as follows:
#   ./bootstrap.sh
#

python3 -m venv venv

source venv/bin/activate

pip install wheel
pip install -r requirements.txt
pip install -r tests/requirements.txt
pip install -e .

mkdir state

pythonz migrate
pythonz createsuperuser
