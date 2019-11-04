#!/bin/sh
# This script will install all the dependencies that this app has at system (server) level, let's said, apt-get packages

ROOT_DIRECTORY="$1"
CHECK_SYSTEM=""

if [ -z "$ROOT_DIRECTORY" ]; then
   # By default, if we do not specify otherwise, we will supouse we are in a server
   ROOT_DIRECTORY="/home/$APP_NAME/deployment/current"
   CHECK_SYSTEM="/home/$APP_NAME/deployment/.sys_already_configured"
fi

if [ "$UBIOME_ENVIRONMENT" = "ci" ]; then
  CHECK_SYSTEM="/var/lib/jenkins/.$APP_NAME-sys_already_configured"
elif [ ! -z "$UBIOME_ENVIRONMENT" ]; then
   # this is when we run this in our local boxes
   CHECK_SYSTEM="$ROOT_DIRECTORY/../.sys_already_configured"
fi

# Check if it is needed to install system dependencies
if [ -f $CHECK_SYSTEM ]; then
  echo "System already configured. Skipping sys_setup.sh"
  echo $CHECK_SYSTEM
  return 0;
fi

#####################  Main ######################
# make sure we execute this script from it's location
cd $ROOT_DIRECTORY

# linux system
sudo apt-get update

sudo apt-get -y install  $(grep -vE "^\s*#" $ROOT_DIRECTORY/private/setup/common/apt-get.dependencies | tr "\n" " ")

# install and set up python vitural env
# sudo pip install virtualenv
# No need to install this since py3 already includes a venv utility

echo "$(date -u +%F_%H.%M.%S)" > $CHECK_SYSTEM
