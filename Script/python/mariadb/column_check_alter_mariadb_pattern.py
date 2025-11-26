#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MariaDB 10.5 컬럼 체크 및 추가 스크립트 (Python 3.11.9)
목적: 지정된 테이블이 존재하는 모든 데이터베이스에서
      지정된 컬럼들이 존재하는지 확인하고, 없으면 추가하는 스크립트

동작 방식:
1. MariaDB 연결 테스트
2. 선택된 방법으로 데이터베이스 목록 가져오기
3. 각 데이터베이스의 대상 테이블에 컬럼 존재 여부 확인
4. 없는 컬럼은 자동으로 추가하고 코멘트 설정
"""

import pymysql
import sys
import os
import re
from typing import List, Dict, Tuple

# ========================================
# MariaDB 서버 접속 정보 설정
# ========================================
DB_HOST = 'localhost'
DB_USER = 'user'
DB_PASS = 'password'

# ========================================
# 대상 테이블 설정 (정규식 패턴)
# ========================================
TARGET_TABLE_PATTERN = r'^TEST_.*_CHATING_PROCESS$'  # 정규식 패턴으로 대상 테이블 지정
#TARGET_TABLE_PATTERN = 'chatbot_doc_summary_log'

# ========================================
# 제외할 테이블 패턴 설정
# ========================================
EXCLUDED_TABLE_PATTERNS = [
    r'.*_BACKUP$',      # _BACKUP으로 끝나는 테이블 제외
    r'.*_TEMP$',        # _TEMP로 끝나는 테이블 제외
    r'.*_OLD$',         # _OLD로 끝나는 테이블 제외
    r'^TEMP_.*',        # TEMP_로 시작하는 테이블 제외
    'ASADAL_CRAWLING_LEARN_LIST',
    # 필요에 따라 추가 패턴을 여기에 추가하세요''
]

# ========================================
# 기준 테이블 설정 (데이터베이스 검색용)
# ========================================
REFERENCE_TABLE = 'chatbot_setup'  # 기준 테이블 (데이터베이스 검색용)

# ========================================
# 데이터베이스 리스트 파일 설정
# ========================================
DB_LIST_FILE = 'db_list.txt'  # 데이터베이스 리스트 파일

# ========================================
# 추가할 컬럼 정의
# ========================================
# COLUMNS 딕셔너리: 컬럼명과 데이터 타입을 정의
# COMMENTS 딕셔너리: 각 컬럼에 대한 설명 코멘트를 정의
COLUMNS = {
    'session_id': 'TEXT DEFAULT NULL',
}

COMMENTS = {
    'session_id': '세션 아이디',
}


# ========================================
# 시스템 데이터베이스 목록 (제외할 DB)
# ========================================
SYSTEM_DBS = {
    'information_schema', 'mysql', 'performance_schema',
    'sys', 'test', 'tmp', 'temp'
}

class MariaDBColumnManager:
    """MariaDB 컬럼 관리 클래스"""

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

    def get_matching_tables(self, database: str, pattern: str) -> List[str]:
        """정규식 패턴에 맞는 테이블 목록 조회 (제외 패턴 적용)"""
        try:
            self.cursor.execute(f"USE `{database}`")
            self.cursor.execute("SHOW TABLES")
            tables = [row[0] for row in self.cursor.fetchall()]

            # 정규식 패턴에 맞는 테이블 필터링
            matching_tables = []
            for table in tables:
                # 포함 패턴 확인
                if re.match(pattern, table):
                    # 제외 패턴 확인
                    is_excluded = False
                    for excluded_pattern in EXCLUDED_TABLE_PATTERNS:
                        if re.match(excluded_pattern, table):
                            is_excluded = True
                            print(f"    🚫 제외된 테이블: {table} (패턴: {excluded_pattern})")
                            break
                    
                    if not is_excluded:
                        matching_tables.append(table)

            return matching_tables
        except Exception as e:
            print(f"  ❌ 테이블 목록 조회 실패: {e}")
            return []

    def table_exists(self, database: str, table_name: str) -> bool:
        """테이블 존재 여부 확인"""
        try:
            self.cursor.execute(f"USE `{database}`")
            self.cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
            return self.cursor.fetchone() is not None
        except Exception as e:
            print(f"  ❌ 테이블 존재 여부 확인 실패: {e}")
            return False

    def column_exists(self, database: str, table_name: str, column_name: str) -> bool:
        """컬럼 존재 여부 확인"""
        try:
            query = """
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s AND column_name = %s
            """
            self.cursor.execute(query, (database, table_name, column_name))
            count = self.cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            print(f"    ❌ 컬럼 존재 여부 확인 실패: {e}")
            return False

    def add_column(self, database: str, table_name: str, column_name: str, column_type: str) -> bool:
        """컬럼 추가"""
        try:
            query = f"ALTER TABLE `{table_name}` ADD COLUMN `{column_name}` {column_type}"
            self.cursor.execute(query)
            return True
        except Exception as e:
            print(f"      ❌ 컬럼 추가 실패: {e}")
            return False

    def add_column_comment(self, database: str, table_name: str, column_name: str,
                          column_type: str, comment: str) -> bool:
        """컬럼 코멘트 추가"""
        try:
            query = f"ALTER TABLE `{table_name}` MODIFY COLUMN `{column_name}` {column_type} COMMENT '{comment}'"
            self.cursor.execute(query)
            return True
        except Exception as e:
            print(f"      ⚠️  코멘트 추가 실패: {e}")
            return False

    def process_database(self, database: str, target_tables: List[str], columns: Dict[str, str],
                        comments: Dict[str, str]) -> Tuple[int, int]:
        """데이터베이스 처리"""
        print(f"▶ {database} 데이터베이스 처리 중...")
        print(f"  🎯 대상 테이블 패턴: {TARGET_TABLE_PATTERN}")
        print(f"  📋 매칭된 테이블: {target_tables}")

        added_count = 0
        existing_count = 0

        for table_name in target_tables:
            print(f"  🎯 테이블 처리: {table_name}")

            for column_name, column_type in columns.items():
                print(f"    🔍 처리 중인 컬럼: '{column_name}'")
                print(f"    🔍 컬럼 데이터 타입: '{column_type}'")

                if self.column_exists(database, table_name, column_name):
                    print(f"    ✅ 컬럼 존재: {column_name}")
                    existing_count += 1
                else:
                    print(f"    ➕ 컬럼 추가: {column_name}")

                    if self.add_column(database, table_name, column_name, column_type):
                        print(f"      ✅ 추가 완료: {column_name}")
                        added_count += 1

                        # 코멘트 추가
                        if column_name in comments and comments[column_name]:
                            if self.add_column_comment(database, table_name, column_name,
                                                     column_type, comments[column_name]):
                                print(f"      ✅ 코멘트 추가 완료: {column_name}")
                            else:
                                print(f"      ⚠️  코멘트 추가 실패: {column_name} (컬럼은 정상 추가됨)")
                    else:
                        print(f"      ❌ 추가 실패: {column_name}")

        return added_count, existing_count

def get_user_choice() -> str:
    """사용자 선택 메뉴"""
    print("🔧 MariaDB 10.5 컬럼 체크 및 추가 스크립트")
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
    manager = MariaDBColumnManager(DB_HOST, DB_USER, DB_PASS)
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
    print(f"🎯 대상 테이블 패턴: {TARGET_TABLE_PATTERN}")
    print(f"🚫 제외할 테이블 패턴: {EXCLUDED_TABLE_PATTERNS}")
    print(f"📋 처리할 컬럼: {list(COLUMNS.keys())}")
    print("")

    # 각 데이터베이스 처리
    total_added = 0
    total_existing = 0

    for database in databases:
        matching_tables = manager.get_matching_tables(database, TARGET_TABLE_PATTERN)
        if matching_tables:
            added, existing = manager.process_database(database, matching_tables, COLUMNS, COMMENTS)
            total_added += added
            total_existing += existing
        else:
            print(f"▶ {database} 데이터베이스 처리 중...")
            print(f"  ❌ {TARGET_TABLE_PATTERN} 패턴에 맞는 테이블을 찾을 수 없습니다.")

    # 결과 출력
    print("")
    print("🎉 컬럼 체크 및 추가 작업 완료!")
    print("📊 처리된 작업:")
    if db_selection_method == "table":
        print(f"   - 기준 테이블: {REFERENCE_TABLE}")
    elif db_selection_method == "file":
        print(f"   - 데이터베이스 리스트 파일: {DB_LIST_FILE}")
    print(f"   - 대상 테이블 패턴: {TARGET_TABLE_PATTERN}")
    print(f"   - 제외할 테이블 패턴: {EXCLUDED_TABLE_PATTERNS}")
    print(f"   - 대상 데이터베이스 수: {len(databases)}")
    print(f"   - 처리된 컬럼 수: {len(COLUMNS)}")
    print(f"   - 각 컬럼: {list(COLUMNS.keys())}")
    print(f"   - 새로 추가된 컬럼: {total_added}개")
    print(f"   - 이미 존재하는 컬럼: {total_existing}개")

    # 연결 해제
    manager.disconnect()

if __name__ == "__main__":
    main()
