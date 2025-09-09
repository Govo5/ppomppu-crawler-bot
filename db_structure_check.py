#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 데이터베이스 구조 확인 도구
"""

import sqlite3

DB_PATH = 'ppomppu_crawl.db'

def check_structure():
    """데이터베이스 구조 확인"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("🔍 데이터베이스 구조 분석")
        print("=" * 50)
        
        # 모든 테이블 조회
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📋 테이블 목록: {tables}")
        
        for table_name in tables:
            table = table_name[0]
            print(f"\n📊 테이블: {table}")
            print("-" * 30)
            
            # 테이블 구조 확인
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            print("컬럼 구조:")
            for col in columns:
                print(f"  {col[1]:15s} {col[2]:10s} {'NOT NULL' if col[3] else 'NULL':8s} {'PK' if col[5] else '':3s}")
            
            # 데이터 개수 확인
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"데이터 개수: {count}개")
            
            # 샘플 데이터 (최대 3개)
            if count > 0:
                cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                samples = cursor.fetchall()
                print("샘플 데이터:")
                for i, sample in enumerate(samples, 1):
                    print(f"  {i}. {sample}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 오류: {e}")

if __name__ == "__main__":
    check_structure()
