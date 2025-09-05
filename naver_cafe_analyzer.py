#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 네이버 카페 종합 분석기
- 카페 URL 입력으로 전체 네트워크 검색
- Selenium 기반 동적 분석
- 사용자 아이디 및 정보 추출
"""

import time
import re
import json
import base64
import urllib.parse
import sqlite3
from datetime import datetime
import getpass

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class NaverCafeAnalyzer:
    def __init__(self):
        self.driver = None
        self.login_id = "hellomeet77@naver.com"
        self.target_url = None
        self.results = []
        self.init_database()
    
    def init_database(self):
        """결과 저장용 데이터베이스 초기화"""
        self.db_file = "cafe_analysis_results.db"
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT,
                analysis_type TEXT,
                found_data TEXT,
                timestamp TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_ids (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                nickname TEXT,
                profile_url TEXT,
                found_location TEXT,
                source_url TEXT,
                timestamp TEXT,
                UNIQUE(user_id, source_url)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ 데이터베이스 초기화 완료")
    
    def setup_selenium(self):
        """Selenium 설정"""
        print("🚀 Chrome 브라우저 설정 중...")
        
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        # 네트워크 로깅 활성화
        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # 네트워크 모니터링 활성화
            self.driver.execute_cdp_cmd('Network.enable', {})
            self.driver.execute_cdp_cmd('Runtime.enable', {})
            
            print("✅ Chrome 설정 완료")
            return True
        except Exception as e:
            print(f"❌ Chrome 설정 실패: {e}")
            return False
    
    def naver_login(self):
        """네이버 로그인"""
        print(f"🔐 네이버 로그인 ({self.login_id})")
        
        try:
            self.driver.get("https://nid.naver.com/nidlogin.login")
            time.sleep(2)
            
            # 아이디 입력
            id_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "id"))
            )
            id_input.clear()
            id_input.send_keys(self.login_id)
            print("✅ 아이디 입력 완료")
            
            print("🔑 브라우저에서 비밀번호를 입력하고 로그인해주세요...")
            print("로그인 완료 후 아무 키나 눌러주세요.")
            input()
            
            # 로그인 확인
            current_url = self.driver.current_url
            if "naver.com" in current_url and "nidlogin" not in current_url:
                print("✅ 로그인 성공")
                return True
            else:
                print("❌ 로그인 실패")
                return False
                
        except Exception as e:
            print(f"❌ 로그인 오류: {e}")
            return False
    
    def analyze_page_content(self, url):
        """페이지 내용 분석"""
        print(f"📄 페이지 내용 분석: {url}")
        
        try:
            self.driver.get(url)
            time.sleep(3)
            
            page_source = self.driver.page_source
            results = {
                'users': [],
                'encoded_data': [],
                'network_requests': [],
                'javascript_data': []
            }
            
            # 1. HTML에서 사용자 정보 추출
            print("   👤 사용자 정보 추출 중...")
            
            # 프로필 링크에서 사용자 ID 추출
            profile_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'MemberProfilePopUp') or contains(@href, 'memberid=')]")
            
            for link in profile_links:
                try:
                    href = link.get_attribute('href')
                    text = link.text.strip()
                    
                    # memberid 추출
                    id_match = re.search(r'memberid=([^&\s"\']+)', href)
                    if id_match:
                        user_id = id_match.group(1)
                        results['users'].append({
                            'user_id': user_id,
                            'nickname': text,
                            'profile_url': href,
                            'method': 'profile_link'
                        })
                        print(f"      → 사용자 발견: {user_id} ({text})")
                except:
                    continue
            
            # 2. 인코딩된 데이터 분석
            print("   🔐 인코딩된 데이터 분석 중...")
            
            # JWT 토큰 분석
            jwt_pattern = r'eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.?[A-Za-z0-9_-]*'
            jwt_tokens = re.findall(jwt_pattern, page_source)
            
            for token in jwt_tokens:
                try:
                    parts = token.split('.')
                    if len(parts) >= 2:
                        payload_data = base64.b64decode(parts[1] + '==').decode('utf-8')
                        results['encoded_data'].append({
                            'type': 'JWT',
                            'token': token[:50] + '...',
                            'payload': payload_data
                        })
                        print(f"      → JWT 토큰: {payload_data}")
                except:
                    continue
            
            # Base64 데이터 분석
            base64_pattern = r'[A-Za-z0-9+/]{20,}={0,2}'
            base64_candidates = re.findall(base64_pattern, page_source)
            
            for candidate in base64_candidates[:5]:  # 상위 5개만
                try:
                    decoded = base64.b64decode(candidate + '==').decode('utf-8', errors='ignore')
                    if len(decoded) > 10 and any(c.isalpha() for c in decoded):
                        results['encoded_data'].append({
                            'type': 'Base64',
                            'encoded': candidate[:30] + '...',
                            'decoded': decoded
                        })
                        print(f"      → Base64: {decoded[:50]}...")
                except:
                    continue
            
            # 3. JavaScript 변수 분석
            print("   🔧 JavaScript 데이터 분석 중...")
            
            try:
                js_result = self.driver.execute_script("""
                    let foundData = [];
                    
                    // 전역 변수에서 사용자 관련 데이터 찾기
                    for (let prop in window) {
                        try {
                            let value = window[prop];
                            if (typeof value === 'string' && value.length > 5 && value.length < 100) {
                                if (value.includes('userid') || value.includes('memberid') || value.includes('nickname')) {
                                    foundData.push({type: 'window_var', name: prop, value: value});
                                }
                            } else if (typeof value === 'object' && value !== null) {
                                let objStr = JSON.stringify(value).toLowerCase();
                                if (objStr.includes('userid') || objStr.includes('memberid')) {
                                    foundData.push({type: 'window_obj', name: prop, value: JSON.stringify(value)});
                                }
                            }
                        } catch(e) {}
                    }
                    
                    return foundData;
                """)
                
                for item in js_result:
                    results['javascript_data'].append(item)
                    print(f"      → JS 데이터: {item['name']} = {item['value'][:50]}...")
            
            except Exception as e:
                print(f"      ❗ JavaScript 분석 오류: {e}")
            
            return results
            
        except Exception as e:
            print(f"❌ 페이지 분석 오류: {e}")
            return None
    
    def analyze_network_requests(self):
        """네트워크 요청 분석"""
        print("🌐 네트워크 요청 분석 중...")
        
        network_data = []
        
        try:
            # Performance 로그 가져오기
            logs = self.driver.get_log('performance')
            
            for log in logs:
                message = json.loads(log['message'])
                
                if message['message']['method'] == 'Network.responseReceived':
                    response_data = message['message']['params']
                    url = response_data.get('response', {}).get('url', '')
                    
                    # 관심있는 URL 패턴 찾기
                    if any(keyword in url.lower() for keyword in ['member', 'user', 'profile', 'article', 'cafe']):
                        network_data.append({
                            'url': url,
                            'response_headers': response_data.get('response', {}).get('headers', {})
                        })
                        print(f"   → 네트워크 요청: {url[:80]}...")
        
        except Exception as e:
            print(f"❗ 네트워크 분석 오류: {e}")
        
        return network_data
    
    def save_results(self, url, results):
        """결과를 데이터베이스에 저장"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            # 사용자 정보 저장
            for user in results.get('users', []):
                cursor.execute('''
                    INSERT OR IGNORE INTO user_ids 
                    (user_id, nickname, profile_url, found_location, source_url, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    user['user_id'],
                    user['nickname'],
                    user['profile_url'],
                    user['method'],
                    url,
                    timestamp
                ))
            
            # 분석 결과 저장
            for category, data in results.items():
                if data:
                    cursor.execute('''
                        INSERT INTO analysis_results 
                        (url, analysis_type, found_data, timestamp)
                        VALUES (?, ?, ?, ?)
                    ''', (url, category, json.dumps(data, ensure_ascii=False), timestamp))
            
            conn.commit()
            print("💾 결과 저장 완료")
        
        except Exception as e:
            print(f"❗ 저장 오류: {e}")
        
        finally:
            conn.close()
    
    def get_analysis_summary(self):
        """분석 결과 요약"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # 사용자 수 집계
        cursor.execute('SELECT COUNT(DISTINCT user_id) FROM user_ids')
        unique_users = cursor.fetchone()[0]
        
        # 상위 사용자들
        cursor.execute('''
            SELECT user_id, nickname, COUNT(*) as count 
            FROM user_ids 
            GROUP BY user_id 
            ORDER BY count DESC 
            LIMIT 10
        ''')
        top_users = cursor.fetchall()
        
        conn.close()
        
        return {
            'unique_users': unique_users,
            'top_users': top_users
        }
    
    def run_analysis(self, target_url):
        """메인 분석 실행"""
        self.target_url = target_url
        
        print("🚀 네이버 카페 종합 분석 시작")
        print("=" * 60)
        print(f"📍 대상 URL: {target_url}")
        print()
        
        try:
            # 1. Selenium 설정
            if not self.setup_selenium():
                return False
            
            # 2. 로그인 (선택사항)
            login_choice = input("로그인을 하시겠습니까? (y/n): ").lower()
            if login_choice == 'y':
                if not self.naver_login():
                    print("⚠️ 로그인 실패, 비로그인 상태로 진행합니다.")
                time.sleep(2)
            
            # 3. 페이지 분석
            results = self.analyze_page_content(target_url)
            
            if results:
                # 4. 네트워크 분석
                network_data = self.analyze_network_requests()
                results['network_requests'] = network_data
                
                # 5. 결과 저장
                self.save_results(target_url, results)
                
                # 6. 결과 출력
                print("\n" + "=" * 60)
                print("📊 분석 결과:")
                print(f"👤 발견된 사용자: {len(results['users'])}명")
                print(f"🔐 인코딩 데이터: {len(results['encoded_data'])}개")
                print(f"🔧 JavaScript 데이터: {len(results['javascript_data'])}개")
                print(f"🌐 네트워크 요청: {len(results['network_requests'])}개")
                
                # 사용자 목록 출력
                if results['users']:
                    print("\n👥 발견된 사용자들:")
                    for i, user in enumerate(results['users'][:10], 1):
                        print(f"   {i:2d}. {user['user_id']} ({user['nickname']})")
                
                # 전체 요약
                summary = self.get_analysis_summary()
                print(f"\n📈 전체 분석 요약:")
                print(f"   총 고유 사용자: {summary['unique_users']}명")
                
                return True
            else:
                print("❌ 분석 실패")
                return False
            
        except Exception as e:
            print(f"❌ 분석 중 오류: {e}")
            return False
        
        finally:
            if self.driver:
                print("\n🔚 브라우저 종료 중...")
                time.sleep(2)
                self.driver.quit()

def main():
    """메인 함수"""
    print("🚀 네이버 카페 종합 분석기")
    print("=" * 40)
    print("📝 이 도구는 다음을 분석합니다:")
    print("   - 사용자 아이디 및 닉네임")
    print("   - 인코딩된 데이터 (JWT, Base64)")
    print("   - JavaScript 변수")
    print("   - 네트워크 요청")
    print()
    
    # URL 입력 받기
    url = input("🔗 분석할 카페 URL을 입력하세요: ").strip()
    
    if not url:
        print("❌ URL이 입력되지 않았습니다.")
        return
    
    if "naver.com" not in url:
        print("❌ 네이버 카페 URL이 아닙니다.")
        return
    
    # 분석 실행
    analyzer = NaverCafeAnalyzer()
    success = analyzer.run_analysis(url)
    
    if success:
        print("✅ 분석 완료!")
        print(f"📁 결과는 '{analyzer.db_file}' 에 저장되었습니다.")
    else:
        print("❌ 분석 실패")

if __name__ == "__main__":
    main()
