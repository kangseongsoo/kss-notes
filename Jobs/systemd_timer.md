# PostgreSQL Health Check - systemd Timer 설치 가이드

## 📋 개요
별도 서버에서 systemd timer를 사용하여 다른 서버의 PostgreSQL 상태를 모니터링하고, 연결 실패 시 SMS 알림을 전송하는 시스템입니다.

## 🔧 설치 단계

### 1. 파일 배치
```bash
# 스크립트를 적절한 위치에 복사
sudo cp postgres_health_check.py /root/Check_SMS/
sudo chmod +x /root/Check_SMS/postgres_health_check.py

# systemd 파일들을 시스템 디렉토리에 복사
sudo cp postgres-health-check.service /etc/systemd/system/
sudo cp postgres-health-check.timer /etc/systemd/system/
```

### 2. PostgreSQL 연결 설정 수정
`/root/Check_SMS/postgres_health_check.py` 파일에서 PostgreSQL 연결 정보를 수정:

```python
POSTGRES_CONFIG = {
    'host': '192.168.1.100',  # 실제 PostgreSQL 서버 IP
    'port': 5432,             # PostgreSQL 포트
    'database': 'postgres',   # 데이터베이스명
    'user': 'postgres',       # 사용자명
    'password': 'your_password'  # 비밀번호
}
```

### 3. 필요한 Python 패키지 설치
```bash
# psycopg2 설치
sudo pip3 install psycopg2-binary

# 또는 requirements.txt 사용
sudo pip3 install -r requirements.txt
```

### 4. 로그 디렉토리 생성
```bash
sudo mkdir -p /var/log/WebHook
sudo chown root:root /var/log/WebHook
```

### 5. systemd 서비스 등록 및 활성화
```bash
# systemd 데몬 리로드
sudo systemctl daemon-reload

# 서비스 파일 등록
sudo systemctl enable postgres-health-check.service

# 타이머 활성화 및 시작
sudo systemctl enable postgres-health-check.timer
sudo systemctl start postgres-health-check.timer
```

## 🚀 서비스 관리 명령어

### 타이머 상태 확인
```bash
# 타이머 상태 확인
sudo systemctl status postgres-health-check.timer

# 다음 실행 시간 확인
sudo systemctl list-timers postgres-health-check.timer
```

### 서비스 상태 확인
```bash
# 서비스 상태 확인
sudo systemctl status postgres-health-check.service

# 최근 실행 로그 확인
sudo journalctl -u postgres-health-check.service -f
```

### 수동 실행
```bash
# 수동으로 헬스체크 실행
sudo systemctl start postgres-health-check.service
```

### 서비스 중지/시작
```bash
# 타이머 중지
sudo systemctl stop postgres-health-check.timer

# 타이머 시작
sudo systemctl start postgres-health-check.timer

# 타이머 비활성화
sudo systemctl disable postgres-health-check.timer
```

## 📊 모니터링

### 로그 확인
```bash
# 애플리케이션 로그
tail -f /var/log/WebHook/PostgreSQL_HealthCheck.log

# systemd 로그
sudo journalctl -u postgres-health-check.service --since "1 hour ago"
```

### 실행 이력 확인
```bash
# 타이머 실행 이력
sudo systemctl list-timers --all | grep postgres

# 서비스 실행 이력
sudo journalctl -u postgres-health-check.service --since "today"
```

## ⚙️ 설정 옵션

### 실행 주기 변경
`/etc/systemd/system/postgres-health-check.timer` 파일에서:

```ini
[Timer]
# 1분마다 실행
OnCalendar=*:0/1:00

# 10분마다 실행  
OnCalendar=*:0/10:00

# 매일 오전 9시에 실행
OnCalendar=daily
```

### 타임아웃 설정
`/etc/systemd/system/postgres-health-check.service` 파일에 추가:

```ini
[Service]
# 30초 타임아웃
TimeoutStartSec=30
```

## 🔍 문제 해결

### 연결 실패 시
1. PostgreSQL 서버 IP 확인
2. 방화벽 설정 확인
3. PostgreSQL 사용자 권한 확인

### SMS 전송 실패 시
1. SMS 스크립트 경로 확인
2. SMS 스크립트 실행 권한 확인
3. 네트워크 연결 상태 확인

### 로그 확인
```bash
# 상세 오류 로그
sudo journalctl -u postgres-health-check.service -l

# 실시간 로그 모니터링
sudo journalctl -u postgres-health-check.service -f
```

## 📱 SMS 알림 예시
PostgreSQL 연결 실패 시:
```
[PostgreSQL 알림] 2024-01-15 14:30:25 - PostgreSQL 서버 연결 실패. 서버 상태를 확인해주세요.
```

## ✅ 확인 사항
- [ ] PostgreSQL 서버 IP 설정 완료
- [ ] SMS 스크립트 경로 확인
- [ ] 로그 디렉토리 생성
- [ ] systemd 서비스 활성화
- [ ] 타이머 실행 확인
