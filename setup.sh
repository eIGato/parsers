#!/usr/bin/env bash

WORKDIR=`dirname $0`
cd $WORKDIR
virtualenv -p python3 .venv
.venv/bin/pip install -r requirements.txt
mkdir results
