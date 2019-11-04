#!/bin/sh
# This script will install all the dependencies that this app has (requirements.txt)

ROOT_DIRECTORY="$1"
if [ -z "$ROOT_DIRECTORY" ]; then
 # By default, if we do not specify otherwise, we will supouse we are in a server
 ROOT_DIRECTORY="/home/$APP_NAME/deployment/current"
fi
#####################  Main ######################
# make sure we execute this script from it's location
cd $ROOT_DIRECTORY

# clean up and rebuild virtutal environment
if [ -d venv ]; then
  rm -rf venv
fi

echo "Creating virtualenv..."
python3.6 -m venv venv
#virtualenv --no-site-packages venv

echo "Activating virtualenv..."
. venv/bin/activate

echo "Updating pip and setuptools from virtualenv..."
python3.6 -m pip install --upgrade pip setuptools

echo "Installing dependencies into virtualenv..."
# install libraries into vitural env
python3.6 -m pip install --no-cache-dir -r $ROOT_DIRECTORY/private/setup/common/requirements.txt

# purge old .pyc files, so we don't have stale caching issues
find . -path ./venv -prune -o -name '*.pyc' -exec rm -f {} +

echo "Deactivating virtualenv..."
# deactivate the venv by default
deactivate
