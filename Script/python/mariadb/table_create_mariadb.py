#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MariaDB 10.5 테이블 생성 스크립트 (Python 3.11.9)
목적: 지정된 테이블이 존재하는 모든 데이터베이스에서
      지정된 테이블이 존재하지 않으면 생성하는 스크립트

동작 방식:
1. MariaDB 연결 테스트
2. 선택된 방법으로 데이터베이스 목록 가져오기
3. 각 데이터베이스에서 대상 테이블 존재 여부 확인
4. 없는 테이블은 자동으로 생성
"""

import pymysql
import sys
import os
from typing import List, Dict, Tuple

# ========================================
# MariaDB 서버 접속 정보 설정
# ========================================
DB_HOST = 'localhost'
DB_USER = 'user'
DB_PASS = 'password'

# ========================================
# 대상 테이블 설정
# ========================================
TARGET_TABLE = 'CRAWLING_LOG'  # 생성할 테이블 이름

# ========================================
# 기준 테이블 설정 (데이터베이스 검색용)
# ========================================
REFERENCE_TABLE = 'chatbot_setup'  # 기준 테이블 (데이터베이스 검색용)

# ========================================
# 데이터베이스 리스트 파일 설정
# ========================================
DB_LIST_FILE = 'db_list.txt'  # 데이터베이스 리스트 파일

# ========================================
# 생성할 테이블 SQL 정의
# ========================================
# 사용자가 이 부분을 수정하여 원하는 테이블을 생성할 수 있습니다
CREATE_TABLE_SQL = """
CREATE TABLE `CRAWLING_LOG` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `chat_bot_id` VARCHAR(255) NULL DEFAULT NULL,
  `mb_id` VARCHAR(255) NULL DEFAULT NULL,
  `mb_name` VARCHAR(255) NULL DEFAULT NULL,
  `subject` VARCHAR(255) NULL DEFAULT NULL,
  `domain` VARCHAR(255) NULL DEFAULT NULL,
  `colle` VARCHAR(255) NULL DEFAULT NULL COMMENT '수집방법',
  `details` VARCHAR(255) NULL DEFAULT NULL COMMENT '상세내역',
  `content_type` VARCHAR(50) NULL DEFAULT NULL,
  `status` VARCHAR(10) NULL DEFAULT NULL COMMENT '상태',
  `start_at` VARCHAR(255) NULL DEFAULT NULL,
  `end_at` DATETIME NULL DEFAULT NULL,
  `pages` VARCHAR(255) NULL DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci COMMENT='크롤링 로그테이블'
"""

# ========================================
# 시스템 데이터베이스 목록 (제외할 DB)
# ========================================
SYSTEM_DBS = {
    'information_schema', 'mysql', 'performance_schema', 
    'sys', 'test', 'tmp', 'temp'
}

class MariaDBTableManager:
    """MariaDB 테이블 관리 클래스"""
    
    def __init__(self, host: str, user: str, password: str):
        self.host = host
        self.user = user
        self.password = password
        self.connection = None
        self.cursor = None
    
    def connect(self) -> bool:
        """MariaDB 연결"""
        try:
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                charset='utf8mb4',
                autocommit=True
            )
            self.cursor = self.connection.cursor()
            print("✅ MariaDB 연결 성공")
            return True
        except Exception as e:
            print(f"❌ MariaDB 연결 실패: {e}")
            return False
    
    def disconnect(self):
        """MariaDB 연결 해제"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
    
    def test_connection(self) -> bool:
        """연결 테스트"""
        try:
            self.cursor.execute("SELECT 1")
            return True
        except Exception as e:
            print(f"❌ 연결 테스트 실패: {e}")
            return False
    
    def get_databases_by_table(self, table_name: str) -> List[str]:
        """특정 테이블이 존재하는 데이터베이스 목록 조회"""
        try:
            query = """
                SELECT DISTINCT table_schema 
                FROM information_schema.tables 
                WHERE table_name = %s
            """
            self.cursor.execute(query, (table_name,))
            databases = [row[0] for row in self.cursor.fetchall()]
            return databases
        except Exception as e:
            print(f"❌ 데이터베이스 조회 실패: {e}")
            return []
    
    def get_databases_from_file(self, file_path: str) -> List[str]:
        """파일에서 데이터베이스 목록 읽기"""
        try:
            if not os.path.exists(file_path):
                print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
                return []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                databases = []
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        databases.append(line)
                return databases
        except Exception as e:
            print(f"❌ 파일 읽기 실패: {e}")
            return []
    
    def get_all_databases(self) -> List[str]:
        """모든 데이터베이스 목록 조회 (시스템DB 제외)"""
        try:
            self.cursor.execute("SHOW DATABASES")
            databases = [row[0] for row in self.cursor.fetchall() 
                        if row[0] not in SYSTEM_DBS]
            return databases
        except Exception as e:
            print(f"❌ 데이터베이스 목록 조회 실패: {e}")
            return []
    
    def table_exists(self, database: str, table_name: str) -> bool:
        """테이블 존재 여부 확인"""
        try:
            query = """
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = %s
            """
            self.cursor.execute(query, (database, table_name))
            count = self.cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            print(f"  ❌ 테이블 존재 여부 확인 실패: {e}")
            return False
    
    def create_table(self, database: str, table_name: str, create_sql: str) -> bool:
        """테이블 생성"""
        try:
            # 데이터베이스 선택
            self.cursor.execute(f"USE `{database}`")
            
            # 테이블 생성
            self.cursor.execute(create_sql)
            return True
        except Exception as e:
            print(f"      ❌ 테이블 생성 실패: {e}")
            return False
    
    def process_database(self, database: str, target_table: str, create_sql: str) -> Tuple[int, int]:
        """데이터베이스 처리"""
        print(f"▶ {database} 데이터베이스 처리 중...")
        print(f"  🎯 대상 테이블: {target_table}")
        
        created_count = 0
        existing_count = 0
        
        if self.table_exists(database, target_table):
            print(f"  ✅ 테이블 존재: {target_table}")
            existing_count += 1
        else:
            print(f"  ➕ 테이블 생성: {target_table}")
            
            if self.create_table(database, target_table, create_sql):
                print(f"      ✅ 생성 완료: {target_table}")
                created_count += 1
            else:
                print(f"      ❌ 생성 실패: {target_table}")
        
        return created_count, existing_count

def get_user_choice() -> str:
    """사용자 선택 메뉴"""
    print("🔧 MariaDB 10.5 테이블 생성 스크립트")
    print("")
    print("📋 데이터베이스 선택 방법을 선택하세요:")
    print("1) 파일에서 데이터베이스 목록 읽기 (db_list.txt)")
    print("2) 특정 테이블이 존재하는 데이터베이스 자동 검색")
    print("")
    
    while True:
        choice = input("선택 (1 또는 2): ").strip()
        if choice in ['1', '2']:
            return choice
        else:
            print("❌ 잘못된 선택입니다. 1 또는 2를 입력하세요.")

def main():
    """메인 함수"""
    # 사용자 선택
    choice = get_user_choice()
    
    if choice == '1':
        db_selection_method = "file"
        print("✅ 파일 기반 방법을 선택했습니다.")
    else:
        db_selection_method = "table"
        print("✅ 테이블 기반 방법을 선택했습니다.")
    
    print("")
    
    # MariaDB 연결
    manager = MariaDBTableManager(DB_HOST, DB_USER, DB_PASS)
    if not manager.connect():
        sys.exit(1)
    
    # 연결 테스트
    print("🔍 MariaDB 연결 테스트 중...")
    if not manager.test_connection():
        print("❌ MariaDB 연결에 실패했습니다. 접속 정보를 확인해주세요.")
        manager.disconnect()
        sys.exit(1)
    
    print("✅ MariaDB 연결 성공")
    print("")
    
    # 데이터베이스 목록 가져오기
    databases = []
    
    if db_selection_method == "table":
        print(f"🔍 {REFERENCE_TABLE} 테이블이 존재하는 데이터베이스 검색 중...")
        databases = manager.get_databases_by_table(REFERENCE_TABLE)
        
        if not databases:
            print(f"❌ {REFERENCE_TABLE} 테이블이 존재하는 데이터베이스를 찾을 수 없습니다.")
            manager.disconnect()
            sys.exit(1)
        
        print(f"✅ {REFERENCE_TABLE} 테이블이 존재하는 데이터베이스:")
        for db in databases:
            print(f"  - {db}")
    
    elif db_selection_method == "file":
        print(f"📖 {DB_LIST_FILE} 파일에서 데이터베이스 목록 읽는 중...")
        databases = manager.get_databases_from_file(DB_LIST_FILE)
        
        if not databases:
            print(f"❌ {DB_LIST_FILE} 파일에서 유효한 데이터베이스 목록을 찾을 수 없습니다.")
            manager.disconnect()
            sys.exit(1)
        
        print(f"✅ {DB_LIST_FILE} 파일에서 읽은 데이터베이스:")
        for db in databases:
            print(f"  - {db}")
    
    print("")
    
    # 설정 정보 출력
    print("📋 사용 클라이언트: pymysql")
    print(f"🎯 데이터베이스 선택 방법: {db_selection_method}")
    if db_selection_method == "table":
        print(f"🎯 기준 테이블: {REFERENCE_TABLE} (데이터베이스 검색용)")
    elif db_selection_method == "file":
        print(f"🎯 데이터베이스 리스트 파일: {DB_LIST_FILE}")
    print(f"🎯 대상 테이블: {TARGET_TABLE} (생성 대상)")
    print("")
    
    # 각 데이터베이스 처리
    total_created = 0
    total_existing = 0
    
    for database in databases:
        created, existing = manager.process_database(database, TARGET_TABLE, CREATE_TABLE_SQL)
        total_created += created
        total_existing += existing
    
    # 결과 출력
    print("")
    print("🎉 테이블 생성 작업 완료!")
    print("📊 처리된 작업:")
    if db_selection_method == "table":
        print(f"   - 기준 테이블: {REFERENCE_TABLE}")
    elif db_selection_method == "file":
        print(f"   - 데이터베이스 리스트 파일: {DB_LIST_FILE}")
    print(f"   - 대상 테이블: {TARGET_TABLE}")
    print(f"   - 대상 데이터베이스 수: {len(databases)}")
    print(f"   - 새로 생성된 테이블: {total_created}개")
    print(f"   - 이미 존재하는 테이블: {total_existing}개")
    
    # 연결 해제
    manager.disconnect()

if __name__ == "__main__":
    main() 