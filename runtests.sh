#!/bin/bash


if [ $1 = 'venv' ];
then
. ../venv/bin/activate
fi

py.test apps
