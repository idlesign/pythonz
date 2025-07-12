#!/bin/bash

# Bootstraps a local development environment.
#
# Run as follows:
#   ./bootstrap.sh
#
set -e

uv sync --locked

mkdir -p state

source .venv/bin/activate

pythonz migrate

export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_PASSWORD=admin
export DJANGO_SUPERUSER_EMAIL=admin@example.com
pythonz createsuperuser

set +e
