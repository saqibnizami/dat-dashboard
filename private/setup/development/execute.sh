#!/bin/sh

ROOT_DIRECTORY=$(dirname $0)/../../..

# make sure we execute this script from it's location
cd $ROOT_DIRECTORY

# activate the environment
. venv/bin/activate

# run the project with development configuration
./index.py --env development
