#!/bin/bash

# 로그 파일의 경로를 사용자로부터 입력받습니다
read -p "로그 파일 경로를 입력하세요: " log_file

# 시작 시간과 끝 시간을 사용자로부터 입력받습니다 (형식: HH)
read -p "시작 시간을 입력하세요 (형식: HH): " start_hour
read -p "끝 시간을 입력하세요 (형식: HH): " end_hour

# 로그 파일을 저장할 디렉토리 경로를 사용자로부터 입력받습니다
read -p "저장할 디렉토리 경로를 입력하세요: " output_dir

# 저장할 디렉토리가 존재하지 않으면 생성합니다
mkdir -p "$output_dir"

# 시간대별로 로그 파일을 추출하여 저장합니다
for hour in $(seq -w $start_hour $end_hour)
do
    start_time="${hour}:00:00"
    end_time="${hour}:59:59"
    output_file="${output_dir}/access_log_hour_${hour}.log"

    # 로그 파일에서 지정한 시간 동안의 로그만 추출하여 저장합니다
    awk -v start="$start_time" -v end="$end_time" '
    {
        # 로그 파일의 시간 부분 추출 (형식: [26/May/2023:12:34:56 +0000])
        match($0, /:([0-9]{2}:[0-9]{2}:[0-9]{2})/, arr)
        log_time = arr[1]

        if (log_time >= start && log_time <= end) {
            print $0
        }
    }' "$log_file" > "$output_file"

    echo "시간대 ${hour}:00:00 ~ ${hour}:59:59 동안의 로그가 $output_file 파일에 저장되었습니다."
done

