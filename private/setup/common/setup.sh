#!/bin/sh
# This script will be the one in charge of configure all the setup

PRIVATE_IP=$(ifconfig eth0 | grep "inet addr:" | awk -F':' '{split($2,ip," "); print ip[1]}')
# for reference: http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-instance-addressing.html#using-instance-addressing-common
PUBLIC_IP=$(curl --silent http://169.254.169.254/latest/meta-data/public-ipv4)

ROOT_DIRECTORY="/home/$APP_NAME/deployment/current/"
# Check if it is needed to install system dependencies
sh /home/$APP_NAME/deployment/current/private/setup/common/sys_setup.sh $ROOT_DIRECTORY

# Always install app dependencies (requirements.txt)
sh /home/$APP_NAME/deployment/current/private/setup/common/app_setup.sh $ROOT_DIRECTORY

sudo mkdir -p /var/log/$APP_NAME
sudo chown $APP_NAME:staff /var/log/$APP_NAME

cd /home/$APP_NAME/deployment/current/private/setup/$UBIOME_ENVIRONMENT/

echo "[Info] Copying upstart-conf and upstart files..."
# Setup upstart service
sudo cp upstart-conf /etc/init/$APP_NAME.conf
sudo sed -i'' 's/{{APP_NAME}}/'$APP_NAME'/g' /etc/init/$APP_NAME.conf

# Configure nginx
sudo cp nginx-site /etc/nginx/sites-available/ubiome
sudo mkdir -p /etc/nginx/location.conf
sudo cp /home/$APP_NAME/deployment/current/private/setup/common/nginx-location /etc/nginx/location.conf/$APP_NAME
sudo sed -i'' 's/<private_ip>/'$PRIVATE_IP'/g' /etc/nginx/sites-available/ubiome
sudo sed -i'' 's/<public_ip>/'$PUBLIC_IP'/g' /etc/nginx/sites-available/ubiome
sudo sed -i'' 's/{{APP_NAME}}/'$APP_NAME'/g' /etc/nginx/location.conf/$APP_NAME
sudo sed -i'' 's/{{APP_PORT}}/'$APP_PORT'/g' /etc/nginx/location.conf/$APP_NAME


sudo ln -fs /etc/nginx/sites-available/ubiome /etc/nginx/sites-enabled/ubiome
sudo rm -f /etc/nginx/sites-enabled/default
