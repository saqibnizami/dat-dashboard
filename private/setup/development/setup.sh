#!/bin/sh

# set up your computer / repo with everything you need to get started coding

####################  Functions  #################

command_exists () {
    type "$1" &> /dev/null ;
}

#####################  Main ######################
ROOT_DIRECTORY=$(dirname $0)/../../..

# make sure we execute this script from it's location
cd $ROOT_DIRECTORY

if command_exists "apt-get"; then
  sh $ROOT_DIRECTORY/private/setup/common/sys_setup.sh $ROOT_DIRECTORY
else
  # probably mac os

  # make sure homebrew is installed
  if ! command_exists brew; then
    ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
  fi

  brew update
  brew install curl
  brew install redis

  # install pip
  if ! command_exists pip; then
    sudo easy_install pip
  fi

fi

# clean up and rebuild virtutal environment
if [ -d venv ]; then
  rm -rf venv
fi

sh $ROOT_DIRECTORY/private/setup/common/app_setup.sh $ROOT_DIRECTORY
