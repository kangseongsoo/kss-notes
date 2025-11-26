#!/bin/bash

# files.txt에서 파일 목록을 읽어옵니다.
while IFS= read -r file; do
  # 파일이 존재하는지 확인합니다.
  if [ -e "$file" ]; then
    # 파일 내용에 포함된 'chat/' 문자열을 'simple_chat/'로 변경합니다.
    sed -i 's|chat\/|simple_chat\/|g' "$file"
  else
    # 파일이 존재하지 않으면 메시지 출력
    echo "File not found: $file"
  fi
done < files.txt
