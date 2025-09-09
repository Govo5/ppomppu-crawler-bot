#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🗄️ 뽐뿌 크롤링 봇 데이터베이스 뷰어
- 저장된 게시글 확인
- 중복 방지 현황 조회
- 데이터베이스 관리 도구
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = 'ppomppu_crawl.db'

def check_db_exists():
    """데이터베이스 파일 존재 확인"""
    if os.path.exists(DB_PATH):
        size = os.path.getsize(DB_PATH)
        print(f"✅ 데이터베이스 파일 존재: {DB_PATH}")
        print(f"📊 파일 크기: {size:,} bytes")
        return True
    else:
        print(f"❌ 데이터베이스 파일 없음: {DB_PATH}")
        return False

def view_all_posts():
    """모든 저장된 게시글 조회"""
    if not check_db_exists():
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 테이블 구조 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"\n📋 테이블 목록: {tables}")
        
        # sent_posts 테이블 조회
        cursor.execute("SELECT COUNT(*) FROM sent_posts")
        total_count = cursor.fetchone()[0]
        print(f"\n📊 총 저장된 기록 수: {total_count}개")
        
        if total_count > 0:
            # 최근 10개 기록 조회
            cursor.execute('''
                SELECT post_id, title, link, sent_time, created_at 
                FROM sent_posts 
                ORDER BY created_at DESC 
                LIMIT 10
            ''')
            
            recent_posts = cursor.fetchall()
            print(f"\n🕒 최근 10개 기록:")
            print("-" * 80)
            
            for i, (post_id, title, link, sent_time, created_at) in enumerate(recent_posts, 1):
                print(f"{i:2d}. ID: {post_id}")
                print(f"    제목: {title[:50]}...")
                print(f"    링크: {link[:60]}...")
                print(f"    전송: {sent_time}")
                print(f"    생성: {created_at}")
                print("-" * 80)
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 데이터베이스 조회 오류: {e}")

def view_hash_types():
    """해시 타입별 통계 조회"""
    if not check_db_exists():
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print(f"\n📈 해시 타입별 통계:")
        print("-" * 50)
        
        # 각 해시 타입별 개수
        hash_types = ['post_id', 'title_', 'link_', 'combo_']
        
        for hash_type in hash_types:
            if hash_type == 'post_id':
                # 순수한 post_id (숫자 또는 12자리 해시)
                cursor.execute("SELECT COUNT(*) FROM sent_posts WHERE post_id NOT LIKE 'title_%' AND post_id NOT LIKE 'link_%' AND post_id NOT LIKE 'combo_%'")
            else:
                cursor.execute("SELECT COUNT(*) FROM sent_posts WHERE post_id LIKE ?", (f'{hash_type}%',))
            
            count = cursor.fetchone()[0]
            print(f"{hash_type:10s}: {count:4d}개")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 해시 통계 조회 오류: {e}")

def search_by_keyword(keyword):
    """키워드로 게시글 검색"""
    if not check_db_exists():
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT post_id, title, link, sent_time 
            FROM sent_posts 
            WHERE title LIKE ? 
            ORDER BY created_at DESC
        ''', (f'%{keyword}%',))
        
        results = cursor.fetchall()
        print(f"\n🔍 '{keyword}' 검색 결과: {len(results)}개")
        
        if results:
            print("-" * 80)
            for i, (post_id, title, link, sent_time) in enumerate(results[:5], 1):
                print(f"{i}. ID: {post_id}")
                print(f"   제목: {title}")
                print(f"   시간: {sent_time}")
                print("-" * 80)
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 검색 오류: {e}")

def cleanup_old_records(days=7):
    """오래된 기록 정리"""
    if not check_db_exists():
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 삭제 전 개수 확인
        cursor.execute("SELECT COUNT(*) FROM sent_posts")
        before_count = cursor.fetchone()[0]
        
        # 7일 이전 기록 삭제
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cursor.execute("DELETE FROM sent_posts WHERE created_at < ?", (cutoff_date,))
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"\n🧹 데이터베이스 정리 완료:")
        print(f"   삭제 전: {before_count}개")
        print(f"   삭제됨: {deleted_count}개")
        print(f"   남은 수: {before_count - deleted_count}개")
        
    except Exception as e:
        print(f"❌ 정리 오류: {e}")

def main():
    """메인 메뉴"""
    print("🗄️ 뽐뿌 크롤링 봇 데이터베이스 뷰어")
    print("=" * 50)
    
    while True:
        print("\n📋 메뉴:")
        print("1. 전체 게시글 조회")
        print("2. 해시 타입별 통계")
        print("3. 키워드 검색")
        print("4. 오래된 기록 정리")
        print("5. 데이터베이스 상태 확인")
        print("0. 종료")
        
        choice = input("\n선택하세요 (0-5): ").strip()
        
        if choice == '1':
            view_all_posts()
        elif choice == '2':
            view_hash_types()
        elif choice == '3':
            keyword = input("검색할 키워드를 입력하세요: ").strip()
            if keyword:
                search_by_keyword(keyword)
        elif choice == '4':
            days = input("몇 일 이전 기록을 삭제할까요? (기본값: 7): ").strip()
            days = int(days) if days.isdigit() else 7
            cleanup_old_records(days)
        elif choice == '5':
            check_db_exists()
        elif choice == '0':
            print("👋 프로그램을 종료합니다.")
            break
        else:
            print("❌ 잘못된 선택입니다.")

if __name__ == "__main__":
    main()
