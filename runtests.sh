#!/bin/bash


if [ $1 = 'venv' ];
then
. ../venv/bin/activate
fi

./manage_dev.py test apps -t .
