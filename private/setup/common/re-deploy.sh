#!/bin/sh

ENV="$1"
APP_NAME="$2"
APP_PORT="$3"

if [ ! -f /home/$APP_NAME/deployment/$APP_NAME-service.tar.bz2 ]; then
 echo "File /home/$APP_NAME/deployment/$APP_NAME-service.tar.bz2 does NOT exist. Nothing to do."
 exit 1
fi

if [ -z "$UBIOME_ENVIRONMENT" ]; then
  echo "Variable UBIOME_ENVIRONMENT is not set. Please define that into /etc/environment. Check https://docs.google.com/document/d/1Nf13C_LuiUl_8jBedpQvXqY4YGOxgH7BS5zmmkfcTE0 for details"
  exit 1
fi

echo "Stopping app and nginx as service...."

echo "Unpacking tar file of project..."
cd /home/$APP_NAME/deployment/
sudo -u $APP_NAME -H sh -c "mkdir temp"
sudo -u $APP_NAME -H sh -c "mv /home/$APP_NAME/deployment/$APP_NAME-service.tar.bz2 /home/$APP_NAME/deployment/temp/"
sudo -u $APP_NAME -H sh -c "cd temp; tar -xjvf $APP_NAME-service.tar.bz2"

# Load the environment variables into metapackage.info
cd /home/$APP_NAME/deployment/temp/
while read -r line; do eval $line; export $(echo $line|cut -d'=' -f1); done < metapackage.info
env|sort

cd /home/$APP_NAME/deployment/
sudo -u $APP_NAME -H sh -c "mkdir /home/$APP_NAME/deployment/versions/$BUILD_DATETIME"
sudo -u $APP_NAME -H sh -c "rm -f /home/$APP_NAME/deployment/temp/$APP_NAME-service.tar.bz2"
sudo -u $APP_NAME -H sh -c "mv /home/$APP_NAME/deployment/temp/* /home/$APP_NAME/deployment/versions/$BUILD_DATETIME/"
sudo -u $APP_NAME -H sh -c "rm -fr /home/$APP_NAME/deployment/temp /home/$APP_NAME/deployment/current"
sudo -u $APP_NAME -H sh -c "ln -s /home/$APP_NAME/deployment/versions/$BUILD_DATETIME/ /home/$APP_NAME/deployment/current"
sudo chgrp -R staff /home/$APP_NAME/deployment/
sudo chmod -R g+xwr /home/$APP_NAME/deployment/

echo "Done setting files of new version in directories..."

export APP_NAME=$APP_NAME
export APP_PORT=$APP_PORT

sh /home/$APP_NAME/deployment/current/private/setup/common/setup.sh

sudo stop $APP_NAME
sudo service nginx stop

echo "Starting app  and nginx as service...."

sudo start $APP_NAME
sudo service nginx start

sudo touch /home/$APP_NAME/heartbeat.txt

if [ ! $UBIOME_ENVIRONMENT = "uat" ]; then
    sh /home/$APP_NAME/deployment/current/private/setup/ci/heartbeat_check.sh "https" "$ENV/dash"
else
    sh /home/$APP_NAME/deployment/current/private/setup/ci/heartbeat_check.sh "http" "$ENV/dash"
fi

if [ $? -eq "1" ]; then
 exit 1
fi

echo "Done!"
echo