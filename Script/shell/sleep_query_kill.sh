#!/bin/bash

# 날짜 및 시간
date=` date +%Y.%m.%d\ %H:%M:%S `

# Sleep 걸린 쿼리 수를 체크할 경계값
THRESHOLD=50

# DB User
USER=user
# DB PassWord
PASS=password

# 현재 slow 걸린 쿼리 수 확인
SLOW_QUERY_COUNT=$(mysql -u$USER -p$PASS -e 'show processlist' | grep -v 'system user' |grep  [0-9] | grep Sleep | awk '{if ($6 > 50) {print $1}}' |wc -l)

# sleep 걸린 쿼리 수가 경계값 이상인 경우 해당 쿼리 kill
if [ $SLOW_QUERY_COUNT -ge $THRESHOLD ]; then
  # Slow 걸린 쿼리 ID 가져오기
  SLOW_QUERY_IDS=$(mysql -u$USER -p$PASS -e 'show processlist' | grep -v 'system user' |grep  [0-9] | grep Sleep | awk '{if ($6 > 50) {print $1}}')

  # sleep 걸린 쿼리 kill
  for ID in $SLOW_QUERY_IDS; do
    mysqladmin -u$USER -p$PASS kill $ID
  done

  # 로그 메시지 출력
  echo "" >> /usr/local/mysql/data/slow-kill.log
  echo "$date" >> /usr/local/mysql/data/slow-kill.log
  echo "$SLOW_QUERY_COUNT slow queries have been killed." >> /usr/local/mysql/data/slow-kill.log
  echo "" >> /usr/local/mysql/data/slow-kill.log
else
  # 로그 메시지 출력
  echo "" >> /usr/local/mysql/data/slow-kill.log
  echo "$date" >> /usr/local/mysql/data/slow-kill.log
  echo "No action taken. Slow query count is below threshold: $SLOW_QUERY_COUNT." >> /usr/local/mysql/data/slow-kill.log
  echo "" >> /usr/local/mysql/data/slow-kill.log
fi