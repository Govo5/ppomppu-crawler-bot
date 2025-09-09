#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🗄️ 통합 데이터베이스 뷰어
- posts 테이블 (p_c.py용)와 sent_posts 테이블 (github_crawler.py용) 모두 지원
"""

import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = 'ppomppu_crawl.db'

def check_tables():
    """사용 가능한 테이블 확인"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]
        
        conn.close()
        return tables
    except:
        return []

def view_posts_table():
    """posts 테이블 조회 (p_c.py용)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM posts")
        total = cursor.fetchone()[0]
        print(f"📊 posts 테이블 총 기록: {total}개")
        
        if total > 0:
            # 최근 20개 조회
            cursor.execute('''
                SELECT id, title, link, timestamp 
                FROM posts 
                ORDER BY timestamp DESC 
                LIMIT 20
            ''')
            
            recent_posts = cursor.fetchall()
            print(f"\n🕒 최근 {len(recent_posts)}개 기록:")
            print("-" * 100)
            
            for i, (post_id, title, link, timestamp) in enumerate(recent_posts, 1):
                # title이 비어있으면 링크에서 게시글 번호 표시
                display_title = title if title else f"게시글 #{post_id}"
                print(f"{i:2d}. ID: {post_id}")
                print(f"    제목: {display_title}")
                print(f"    링크: {link}")
                print(f"    시간: {timestamp}")
                print("-" * 100)
        
        conn.close()
        
    except Exception as e:
        print(f"❌ posts 테이블 조회 오류: {e}")

def view_sent_posts_table():
    """sent_posts 테이블 조회 (github_crawler.py용)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM sent_posts")
        total = cursor.fetchone()[0]
        print(f"📊 sent_posts 테이블 총 기록: {total}개")
        
        if total > 0:
            # 최근 20개 조회
            cursor.execute('''
                SELECT post_id, title, link, sent_time, created_at 
                FROM sent_posts 
                ORDER BY created_at DESC 
                LIMIT 20
            ''')
            
            recent_posts = cursor.fetchall()
            print(f"\n🕒 최근 {len(recent_posts)}개 기록:")
            print("-" * 100)
            
            for i, (post_id, title, link, sent_time, created_at) in enumerate(recent_posts, 1):
                print(f"{i:2d}. ID: {post_id}")
                print(f"    제목: {title[:60]}...")
                print(f"    링크: {link[:70]}...")
                print(f"    전송: {sent_time}")
                print(f"    생성: {created_at}")
                print("-" * 100)
        
        conn.close()
        
    except Exception as e:
        print(f"❌ sent_posts 테이블 조회 오류: {e}")

def analyze_posts_duplicates():
    """posts 테이블의 중복 분석"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 중복 ID 확인
        cursor.execute('''
            SELECT id, COUNT(*) as count 
            FROM posts 
            GROUP BY id 
            HAVING COUNT(*) > 1 
            ORDER BY count DESC
        ''')
        
        duplicates = cursor.fetchall()
        print(f"\n🔄 중복된 게시글 ID: {len(duplicates)}개")
        
        if duplicates:
            print("상위 10개 중복:")
            for post_id, count in duplicates[:10]:
                print(f"  ID {post_id}: {count}번 저장됨")
        
        # 시간대별 분석
        cursor.execute('''
            SELECT DATE(timestamp) as date, COUNT(*) as count
            FROM posts 
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
            LIMIT 7
        ''')
        
        daily_stats = cursor.fetchall()
        print(f"\n📅 최근 7일 저장 현황:")
        for date, count in daily_stats:
            print(f"  {date}: {count}개")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 중복 분석 오류: {e}")

def main():
    """메인 함수"""
    print("🗄️ 통합 데이터베이스 뷰어")
    print("=" * 50)
    
    if not os.path.exists(DB_PATH):
        print(f"❌ 데이터베이스 파일 없음: {DB_PATH}")
        return
    
    print(f"✅ DB 파일: {DB_PATH}")
    print(f"📏 파일 크기: {os.path.getsize(DB_PATH):,} bytes")
    
    # 테이블 확인
    tables = check_tables()
    print(f"📋 사용 가능한 테이블: {tables}")
    
    while True:
        print("\n📋 메뉴:")
        if 'posts' in tables:
            print("1. posts 테이블 조회 (p_c.py용)")
            print("2. posts 중복 분석")
        if 'sent_posts' in tables:
            print("3. sent_posts 테이블 조회 (github_crawler.py용)")
        print("4. 데이터베이스 구조 확인")
        print("0. 종료")
        
        choice = input("\n선택하세요: ").strip()
        
        if choice == '1' and 'posts' in tables:
            view_posts_table()
        elif choice == '2' and 'posts' in tables:
            analyze_posts_duplicates()
        elif choice == '3' and 'sent_posts' in tables:
            view_sent_posts_table()
        elif choice == '4':
            os.system('python db_structure_check.py')
        elif choice == '0':
            print("👋 프로그램을 종료합니다.")
            break
        else:
            print("❌ 잘못된 선택입니다.")

if __name__ == "__main__":
    main()
