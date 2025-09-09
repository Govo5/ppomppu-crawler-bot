#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚡ 빠른 데이터베이스 확인 도구
"""

import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = 'ppomppu_crawl.db'

def quick_check():
    """빠른 데이터베이스 상태 확인"""
    print("⚡ 뽐뿌 크롤링 봇 DB 빠른 확인")
    print("=" * 40)
    
    # 파일 존재 확인
    if not os.path.exists(DB_PATH):
        print("❌ 데이터베이스 파일이 없습니다.")
        return
    
    print(f"✅ DB 파일: {DB_PATH}")
    print(f"📏 파일 크기: {os.path.getsize(DB_PATH):,} bytes")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 총 기록 수
        cursor.execute("SELECT COUNT(*) FROM sent_posts")
        total = cursor.fetchone()[0]
        print(f"📊 총 기록 수: {total:,}개")
        
        if total > 0:
            # 최근 24시간 기록
            yesterday = datetime.now() - timedelta(hours=24)
            cursor.execute("SELECT COUNT(*) FROM sent_posts WHERE created_at > ?", (yesterday,))
            recent = cursor.fetchone()[0]
            print(f"🕐 최근 24시간: {recent}개")
            
            # 최신 기록
            cursor.execute("SELECT title, sent_time FROM sent_posts ORDER BY created_at DESC LIMIT 1")
            latest = cursor.fetchone()
            if latest:
                print(f"🔔 최신 기록: {latest[0][:30]}... ({latest[1]})")
            
            # 해시 타입별 개수
            print(f"\n📈 해시 타입별:")
            
            # post_id (순수)
            cursor.execute("SELECT COUNT(*) FROM sent_posts WHERE post_id NOT LIKE 'title_%' AND post_id NOT LIKE 'link_%' AND post_id NOT LIKE 'combo_%'")
            post_id_count = cursor.fetchone()[0]
            print(f"   post_id: {post_id_count}개")
            
            # title_hash
            cursor.execute("SELECT COUNT(*) FROM sent_posts WHERE post_id LIKE 'title_%'")
            title_count = cursor.fetchone()[0]
            print(f"   title_hash: {title_count}개")
            
            # link_hash
            cursor.execute("SELECT COUNT(*) FROM sent_posts WHERE post_id LIKE 'link_%'")
            link_count = cursor.fetchone()[0]
            print(f"   link_hash: {link_count}개")
            
            # combo_hash
            cursor.execute("SELECT COUNT(*) FROM sent_posts WHERE post_id LIKE 'combo_%'")
            combo_count = cursor.fetchone()[0]
            print(f"   combo_hash: {combo_count}개")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ DB 조회 오류: {e}")

if __name__ == "__main__":
    quick_check()
