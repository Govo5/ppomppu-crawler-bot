#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔇 조용한 메시지 테스트 도구
- 알림 비활성화 테스트
"""

import requests
import json
from datetime import datetime

# 텔레그램 설정 (github_crawler.py와 동일)
TELEGRAM_TOKEN = '7250382833:AAGjJpqkln_zsISDO-AYrEmvNFmwmF98gZs'
CHAT_ID = '59277305'

def send_test_message(with_notification=False):
    """테스트 메시지 전송"""
    current_time = datetime.now().strftime('%H:%M:%S')
    
    if with_notification:
        message = f"🔔 일반 메시지 (알림 있음) - {current_time}"
        disable_notification = False
    else:
        message = f"🔇 조용한 메시지 (알림 없음) - {current_time}"
        disable_notification = True
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        'chat_id': CHAT_ID,
        'text': message,
        'disable_notification': disable_notification,
        'parse_mode': 'HTML'
    }
    
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            print(f"✅ 메시지 전송 성공: {message}")
            return True
        else:
            print(f"❌ 전송 실패: {response.status_code}")
            print(f"응답: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 오류: {e}")
        return False

def main():
    """메인 함수"""
    print("🔇 텔레그램 조용한 메시지 테스트")
    print("=" * 40)
    
    while True:
        print("\n📋 테스트 메뉴:")
        print("1. 조용한 메시지 전송 (알림 없음)")
        print("2. 일반 메시지 전송 (알림 있음)")
        print("3. 연속 테스트 (조용함 → 일반)")
        print("0. 종료")
        
        choice = input("\n선택하세요 (0-3): ").strip()
        
        if choice == '1':
            send_test_message(with_notification=False)
        elif choice == '2':
            send_test_message(with_notification=True)
        elif choice == '3':
            print("\n🔇 조용한 메시지 전송...")
            send_test_message(with_notification=False)
            print("잠시 후...")
            import time
            time.sleep(3)
            print("🔔 일반 메시지 전송...")
            send_test_message(with_notification=True)
        elif choice == '0':
            print("👋 테스트를 종료합니다.")
            break
        else:
            print("❌ 잘못된 선택입니다.")

if __name__ == "__main__":
    main()
