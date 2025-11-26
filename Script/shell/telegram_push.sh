#!/bin/bash

if [ $# -ne 2 ]
then
  echo
  echo "Usage"
  echo "$0 {HOSTNAME} {MESSAGES}"
  echo
  echo "example)"
  echo "$0 \"hostname\" \"/home/ partition check\""
  echo
  exit 0
fi

# info telegram
ID=""
API_TOKEN=""
URL=""

# Date
DATE="$(date "+%Y-%m-%d %H:%M")"

# writ message
TEXT="${DATE} [$1] $2"

# Send message
curl -s -d "chat_id=${ID}&text=${TEXT}" ${URL} > /dev/null