#!/bin/bash

#
# Run as follows:
#   ./runtests.sh
#   ./runtests.sh novenv
#

if [[ $1 != 'novenv' ]]; then

    echo "Trying to use virtual environment '../venv' ..."

    . ../venv/bin/activate

else

    echo "Not using virtual environment ..."

fi

py.test
