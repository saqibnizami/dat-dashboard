#!/bin/sh

ENV="$1"

if [ -z "$ENV" ]; then
 # By default, if we does not specify otherwise, we will deploy on uat
 ENV="uat.ubiome.com"
fi

ROOT_DIRECTORY=$(dirname $0)/../../..

# make sure we execute this script from it's location
cd $ROOT_DIRECTORY

echo "[Info] Packing project excluding test files and venv"
tar --exclude-vcs --exclude=test* --exclude=venv -jcvf $APP_NAME-service.tar.bz2 .

echo "[Info] Uploading file to $ENV: "
rsync $APP_NAME-service.tar.bz2 jenkins@$ENV:/home/$APP_NAME/deployment/
rsync private/setup/common/re-deploy.sh jenkins@$ENV:/home/$APP_NAME/deployment/

echo "Running re-deploy...."
ssh jenkins@$ENV "cd /home/$APP_NAME/deployment/; sh -x re-deploy.sh $ENV $APP_NAME $APP_PORT"
RETVAL=$?
ssh jenkins@$ENV "cd /home/$APP_NAME/deployment/; rm re-deploy.sh"
exit $RETVAL