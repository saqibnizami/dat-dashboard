#!/bin/sh

ROOT_DIRECTORY="$1"
if [ -z "$ROOT_DIRECTORY" ]; then
 echo "Jenkins must provide the current directory: $0 \$\{WORKSPACE\}/<project-name>"
 exit 1
fi

# make sure we execute this script from it's location
cd $ROOT_DIRECTORY

# Check if it is needed to install system dependencies
sh $ROOT_DIRECTORY/private/setup/common/sys_setup.sh $ROOT_DIRECTORY

# Always install app dependencies (requirements.txt)
sh $ROOT_DIRECTORY/private/setup/common/app_setup.sh $ROOT_DIRECTORY
