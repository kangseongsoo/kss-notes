#!/bin/bash

SOURCE_LIST="source_file_list.txt"
TARGET_LIST="list_dir.txt"
LOG_DIR="./logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${LOG_DIR}/delete_log_${TIMESTAMP}.log"

mkdir -p "$LOG_DIR"
echo -e "🗑️ 삭제 작업 시작: $(date)\n" | tee -a "$LOG_FILE"

# 파일 유효성 검사
if [ ! -f "$SOURCE_LIST" ]; then
    echo "❌ Error: $SOURCE_LIST 파일이 없습니다." | tee -a "$LOG_FILE"
    exit 1
fi

if [ ! -f "$TARGET_LIST" ]; then
    echo "❌ Error: $TARGET_LIST 파일이 없습니다." | tee -a "$LOG_FILE"
    exit 1
fi

# 도메인 리스트 순회
while IFS= read -r domain; do
    [[ -z "$domain" || "$domain" =~ ^# ]] && continue

    echo "🔹 대상 도메인: $domain" | tee -a "$LOG_FILE"

    # 소스 파일 리스트 순회
    while IFS= read -r full_source_path; do
        [[ -z "$full_source_path" || "$full_source_path" =~ ^# ]] && continue

        # 상대 경로 계산
        relative_path=$(echo "$full_source_path" | sed -E 's|^/home/[^/]+/||')
        target_path="/home/$domain/$relative_path"

        # 파일 또는 디렉터리 존재 여부 확인 후 삭제
        if [ -e "$target_path" ]; then
            echo "🗑️ 삭제: $target_path" | tee -a "$LOG_FILE"
            rm -rf "$target_path" >> "$LOG_FILE" 2>&1
        else
            echo "⚠️ 없음 (건너뜀): $target_path" | tee -a "$LOG_FILE"
        fi

    done < "$SOURCE_LIST"

    echo "✅ $domain 삭제 완료" | tee -a "$LOG_FILE"
    echo "-----------------------------" | tee -a "$LOG_FILE"
done < "$TARGET_LIST"

echo -e "\n🎉 모든 삭제 완료: $(date)" | tee -a "$LOG_FILE"
echo "📁 로그 파일 저장 위치: $LOG_FILE"
