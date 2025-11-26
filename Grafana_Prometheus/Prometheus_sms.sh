#!/bin/bash

# SMS 전송 API URL
SMS_SEND_URL="http://apiserver/smssend.php"
CONTACTS=("" "")  # 여러 개의 연락처

# 로그 파일 경로
LOG_FILE="/var/log/chatbot/WebHook.log"

# 메시지 전송 함수
send_sms() {
    local message="$1"
    for phone in "${CONTACTS[@]}"; do
        RESPONSE=$(curl -X POST -d "msg=${message}" -d "phone=${phone}" "${SMS_SEND_URL}" -s)
        
        # 응답 확인 및 로깅
        echo "$(date) - [Prometheus_sms] Alert sent to ${phone}: ${message}" >> ${LOG_FILE}
        echo "$(date) - [Prometheus_sms] SMS API Response: ${RESPONSE}" >> ${LOG_FILE}
    done
}

# 메시지 직접 전송
send_sms "$1"
