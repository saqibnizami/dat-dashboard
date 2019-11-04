#!/bin/sh

PROTOCOL="$1"
HOST="$2"

SECONDS=0
MAX=60
echo "[Info] Start checking app $PROTOCOL://$HOST/heartbeat..."
while [ $SECONDS -lt $MAX ]; do
    printf "."
    sleep 1
    if $(curl --output /dev/null --silent --head --fail --insecure $PROTOCOL://$HOST/heartbeat ); then
      echo
      echo "[Info] Check of app Heartbeat OK!"
      break
    else
      SECONDS=$((SECONDS+1))
      if [ $(($SECONDS % 20)) -eq "0" ]; then
         printf "(${SECONDS} seconds waited)"
         echo
      fi
    fi
done
if  [ $SECONDS -eq $MAX ]; then
  echo "[Error] Timeout checking app Heartbeat"
  exit 1
fi

