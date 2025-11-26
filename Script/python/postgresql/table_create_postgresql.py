#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL 테이블 생성 스크립트 (Python 3.11.9)
목적: 지정된 테이블이 존재하는 모든 데이터베이스에서
      지정된 테이블이 존재하지 않으면 생성하는 스크립트

동작 방식:
1. PostgreSQL 연결 테스트
2. 선택된 방법으로 데이터베이스 목록 가져오기
3. 각 데이터베이스에서 대상 테이블 존재 여부 확인
4. 없는 테이블은 자동으로 생성
"""

import psycopg2
import sys
import os
from typing import List, Dict, Tuple

# ========================================
# PostgreSQL 서버 접속 정보 설정
# ========================================
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_USER = 'postgres'
DB_PASS = 'password'

# ========================================
# 대상 테이블 설정
# ========================================
TARGET_TABLES = [
    'translation_log',
]  # 생성할 테이블 목록

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
# TranslationLog 테이블 생성 SQL
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS "translation_log" (
  "id" SERIAL PRIMARY KEY,
  "domain" TEXT NOT NULL,
  "url" TEXT NOT NULL,
  "trans_type" VARCHAR(20) NOT NULL,
  "target_lang" VARCHAR(10) NOT NULL,
  "model" VARCHAR(50) NOT NULL,
  "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS "idx_translation_log_domain" ON "translation_log" ("domain");
CREATE INDEX IF NOT EXISTS "idx_translation_log_target_lang" ON "translation_log" ("target_lang");
CREATE INDEX IF NOT EXISTS "idx_translation_log_created_at" ON "translation_log" ("created_at");
"""

# ========================================
# 시스템 데이터베이스 목록 (제외할 DB)
# ========================================
SYSTEM_DBS = {
    'postgres', 'template0', 'template1', 'information_schema',
    'pg_catalog', 'pg_toast', 'pg_temp_1', 'pg_toast_temp_1'
}

class PostgreSQLTableManager:
    """PostgreSQL 테이블 관리 클래스"""
    
    def __init__(self, host: str, port: str, user: str, password: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.connection = None
        self.cursor = None
    
    def connect(self) -> bool:
        """PostgreSQL 연결"""
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database='postgres'  # 기본 데이터베이스에 연결
            )
            self.connection.autocommit = True
            self.cursor = self.connection.cursor()
            print("✅ PostgreSQL 연결 성공")
            return True
        except Exception as e:
            print(f"❌ PostgreSQL 연결 실패: {e}")
            return False
    
    def disconnect(self):
        """PostgreSQL 연결 해제"""
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
            # 모든 데이터베이스 목록을 가져온 후 각각에서 테이블 존재 여부 확인
            all_databases = self.get_all_databases()
            databases_with_table = []
            
            print(f"🔍 {len(all_databases)}개 데이터베이스에서 '{table_name}' 테이블 검색 중...")
            
            for database in all_databases:
                try:
                    # 각 데이터베이스에 연결하여 테이블 존재 여부 확인
                    temp_conn = psycopg2.connect(
                        host=self.host,
                        port=self.port,
                        user=self.user,
                        password=self.password,
                        database=database
                    )
                    temp_cursor = temp_conn.cursor()
                    
                    query = """
                        SELECT COUNT(*) 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' AND table_name = %s
                    """
                    temp_cursor.execute(query, (table_name,))
                    count = temp_cursor.fetchone()[0]
                    
                    if count > 0:
                        databases_with_table.append(database)
                        print(f"  ✅ {database}: '{table_name}' 테이블 발견")
                    
                    temp_cursor.close()
                    temp_conn.close()
                    
                except Exception as db_error:
                    print(f"  ⚠️  {database}: 연결 실패 - {db_error}")
                    continue
            
            return databases_with_table
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
            self.cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false")
            databases = [row[0] for row in self.cursor.fetchall() 
                        if row[0] not in SYSTEM_DBS]
            return databases
        except Exception as e:
            print(f"❌ 데이터베이스 목록 조회 실패: {e}")
            return []
    
    def table_exists(self, database: str, table_name: str) -> bool:
        """테이블 존재 여부 확인"""
        try:
            # 해당 데이터베이스에 연결
            temp_conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=database
            )
            temp_cursor = temp_conn.cursor()
            
            query = """
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = %s
            """
            temp_cursor.execute(query, (table_name,))
            count = temp_cursor.fetchone()[0]
            
            temp_cursor.close()
            temp_conn.close()
            
            return count > 0
        except Exception as e:
            print(f"  ❌ 테이블 존재 여부 확인 실패: {e}")
            return False
    
    def create_table(self, database: str, table_name: str, create_sql: str) -> bool:
        """테이블 생성"""
        try:
            # 해당 데이터베이스에 연결
            temp_conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=database
            )
            temp_conn.autocommit = True
            temp_cursor = temp_conn.cursor()
            
            # 테이블 생성
            temp_cursor.execute(create_sql)
            
            temp_cursor.close()
            temp_conn.close()
            
            return True
        except Exception as e:
            print(f"      ❌ 테이블 생성 실패: {e}")
            return False
    
    def process_database(self, database: str, target_tables: List[str], create_sql: str) -> Tuple[int, int]:
        """데이터베이스 처리"""
        print(f"▶ {database} 데이터베이스 처리 중...")
        print(f"  🎯 대상 테이블: {target_tables}")
        
        created_count = 0
        existing_count = 0
        
        # 모든 테이블을 한 번에 생성 (의존성 순서 고려)
        print(f"  📝 테이블 및 인덱스 생성 중...")
        if self.create_table(database, "all_tables", create_sql):
            print(f"      ✅ 모든 테이블 생성 완료")
            created_count = len(target_tables)
        else:
            print(f"      ❌ 테이블 생성 실패")
            # 개별 테이블 존재 여부 확인
            for table_name in target_tables:
                if self.table_exists(database, table_name):
                    print(f"  ✅ 테이블 존재: {table_name}")
                    existing_count += 1
                else:
                    print(f"  ❌ 테이블 없음: {table_name}")
        
        return created_count, existing_count

def get_user_choice() -> str:
    """사용자 선택 메뉴"""
    print("🔧 PostgreSQL 테이블 생성 스크립트")
    print("")
    print("📋 데이터베이스 선택 방법을 선택하세요:")
    print("1) 파일에서 데이터베이스 목록 읽기 (db_list.txt)")
    print("2) 특정 테이블이 존재하는 데이터베이스 자동 검색")
    print("3) 모든 데이터베이스 (시스템DB 제외)")
    print("")
    
    while True:
        choice = input("선택 (1, 2 또는 3): ").strip()
        if choice in ['1', '2', '3']:
            return choice
        else:
            print("❌ 잘못된 선택입니다. 1, 2 또는 3을 입력하세요.")

def main():
    """메인 함수"""
    # 사용자 선택
    choice = get_user_choice()
    
    if choice == '1':
        db_selection_method = "file"
        print("✅ 파일 기반 방법을 선택했습니다.")
    elif choice == '2':
        db_selection_method = "table"
        print("✅ 테이블 기반 방법을 선택했습니다.")
    else:
        db_selection_method = "all"
        print("✅ 모든 데이터베이스 방법을 선택했습니다.")
    
    print("")
    
    # PostgreSQL 연결
    manager = PostgreSQLTableManager(DB_HOST, DB_PORT, DB_USER, DB_PASS)
    if not manager.connect():
        sys.exit(1)
    
    # 연결 테스트
    print("🔍 PostgreSQL 연결 테스트 중...")
    if not manager.test_connection():
        print("❌ PostgreSQL 연결에 실패했습니다. 접속 정보를 확인해주세요.")
        manager.disconnect()
        sys.exit(1)
    
    print("✅ PostgreSQL 연결 성공")
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
    
    elif db_selection_method == "all":
        print("🔍 모든 데이터베이스 목록 조회 중...")
        databases = manager.get_all_databases()
        
        if not databases:
            print("❌ 데이터베이스를 찾을 수 없습니다.")
            manager.disconnect()
            sys.exit(1)
        
        print(f"✅ 조회된 데이터베이스:")
        for db in databases:
            print(f"  - {db}")
    
    print("")
    
    # 설정 정보 출력
    print("📋 사용 클라이언트: psycopg2")
    print(f"🎯 데이터베이스 선택 방법: {db_selection_method}")
    if db_selection_method == "table":
        print(f"🎯 기준 테이블: {REFERENCE_TABLE} (데이터베이스 검색용)")
    elif db_selection_method == "file":
        print(f"🎯 데이터베이스 리스트 파일: {DB_LIST_FILE}")
    elif db_selection_method == "all":
        print("🎯 대상: 모든 데이터베이스 (시스템DB 제외)")
    print(f"🎯 대상 테이블: {TARGET_TABLES} (생성 대상)")
    print("")
    
    # 각 데이터베이스 처리
    total_created = 0
    total_existing = 0
    
    for database in databases:
        created, existing = manager.process_database(database, TARGET_TABLES, CREATE_TABLE_SQL)
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
    elif db_selection_method == "all":
        print("   - 대상: 모든 데이터베이스 (시스템DB 제외)")
    print(f"   - 대상 테이블: {TARGET_TABLES}")
    print(f"   - 대상 데이터베이스 수: {len(databases)}")
    print(f"   - 새로 생성된 테이블: {total_created}개")
    print(f"   - 이미 존재하는 테이블: {total_existing}개")
    
    # 연결 해제
    manager.disconnect()

if __name__ == "__main__":
    main()
