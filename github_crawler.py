import requests
from bs4 import BeautifulSoup
import os
import re
import sqlite3
import json
from datetime import datetime, timedelta

# 환경변수에서 텔레그램 설정 가져오기 (테스트용 기본값 포함)
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN') or '7250382833:AAGjJpqkln_zsISDO-AYrEmvNFmwmF98gZs'
CHAT_ID = os.getenv('CHAT_ID') or '59277305'

# 데이터베이스 파일 경로
DB_PATH = 'ppomppu_crawl.db'

def init_database():
    """데이터베이스 초기화"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sent_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id TEXT UNIQUE,
            title TEXT,
            link TEXT,
            sent_time TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def is_post_already_sent(post_id):
    """게시글이 이미 전송되었는지 확인"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT 1 FROM sent_posts WHERE post_id = ?', (post_id,))
    exists = cursor.fetchone() is not None
    
    conn.close()
    return exists

def save_sent_post(post_id, title, link):
    """전송한 게시글 정보 저장"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO sent_posts (post_id, title, link, sent_time)
            VALUES (?, ?, ?, ?)
        ''', (post_id, title, link, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        conn.commit()
        print(f"📝 전송 기록 저장: {post_id}")
    except sqlite3.IntegrityError:
        print(f"⚠️ 이미 저장된 게시글: {post_id}")
    
    conn.close()

def cleanup_old_posts(days=7):
    """오래된 게시글 기록 정리 (기본 7일)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cutoff_date = datetime.now() - timedelta(days=days)
    cursor.execute('DELETE FROM sent_posts WHERE created_at < ?', (cutoff_date,))
    
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    
    if deleted_count > 0:
        print(f"🧹 {deleted_count}개의 오래된 기록 정리")

def send_telegram_message(message, image_url=None, keyboard=None):
    """텔레그램 메시지 전송 (이미지 및 인라인 키보드 지원)"""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ 텔레그램 설정이 없습니다.")
        return False
    
    try:
        # 이미지가 있으면 사진과 함께 전송
        if image_url:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
            data = {
                'chat_id': CHAT_ID,
                'photo': image_url,
                'caption': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True,   # 링크 미리보기 팝업 비활성화 (강화)
            }
            if keyboard:
                data['reply_markup'] = keyboard
        else:
            # 텍스트만 전송 (disable_web_page_preview 강화)
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            data = {
                'chat_id': CHAT_ID,
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True,   # 링크 미리보기 팝업 비활성화 (필수)
            }
            if keyboard:
                data['reply_markup'] = keyboard
        
        # 항상 JSON으로 전송하여 disable_web_page_preview가 확실히 작동하도록 함
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, json=data, headers=headers, timeout=30)
        if response.status_code == 200:
            print("✅ 텔레그램 메시지 전송 성공")
            return True
        else:
            print(f"❌ 텔레그램 전송 실패: {response.status_code}")
            print(f"📄 응답: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ 텔레그램 전송 오류: {e}")
        return False

def crawl_ppomppu():
    """뽐뿌 크롤링 함수 (GitHub Actions용)"""
    print("🚀 GitHub Actions에서 뽐뿌 크롤링 시작:", datetime.now())
    
    # 데이터베이스 초기화 및 정리
    init_database()
    cleanup_old_posts(7)  # 7일 이상 된 기록 정리
    
    # 뽐뿌 URL - 정확한 경로 사용
    URL = 'https://www.ppomppu.co.kr/zboard/zboard.php?id=ppomppu'
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(URL, headers=headers, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 다양한 셀렉터 시도
        rows = soup.select('tr.baseList')
        if not rows:
            rows = soup.select('tr.list0, tr.list1')
        if not rows:
            rows = soup.select('tr[bgcolor]')
        if not rows:
            rows = soup.select('table tr')[2:]  # 헤더 제외
        
        print(f"📊 찾은 게시글 수: {len(rows)}")
        
        new_posts = []
        now = datetime.now()
        
        for row in rows[:20]:  # 최신 20개만 확인 (증가)
            try:
                # 제목과 링크 가져오기 (다양한 방식 시도)
                title_cell = row.select_one('td.title')
                if not title_cell:
                    title_cell = row.select_one('td[width="50%"]')
                if not title_cell:
                    title_cell = row.select_one('td.list_title')
                if not title_cell:
                    # 가장 긴 텍스트를 가진 td 찾기
                    all_tds = row.select('td')
                    title_cell = max(all_tds, key=lambda x: len(x.get_text(strip=True))) if all_tds else None
                
                if not title_cell:
                    continue
                
                link_tag = title_cell.select_one('a')
                if not link_tag:
                    continue
                
                # 제목 추출 - 개선된 방법
                title = ""
                
                # 방법 1: 링크 텍스트 (공백 정리)
                title = link_tag.get_text(strip=True)
                title = re.sub(r'\s+', ' ', title)  # 중복 공백 제거
                
                # 방법 2: title 속성 사용
                if not title or len(title) < 5:
                    title = link_tag.get('title', '').strip()
                
                # 방법 3: img의 alt 속성 사용
                if not title or len(title) < 5:
                    img_tag = title_cell.select_one('img')
                    if img_tag:
                        title = img_tag.get('alt', '').strip()
                        if not title:
                            title = img_tag.get('title', '').strip()
                
                # 방법 4: 전체 td 내용 사용 (정리 후)
                if not title or len(title) < 5:
                    title = title_cell.get_text(strip=True)
                    title = re.sub(r'\s+', ' ', title)
                    # 불필요한 부분 제거
                    title = re.sub(r'(new|N|HOT|추천|\d+:\d+)', '', title, flags=re.IGNORECASE).strip()
                
                # 제목이 여전히 비어있으면 건너뛰기
                if not title or len(title) < 5:
                    print(f"❌ 제목을 찾을 수 없음: td={title_cell.get_text(strip=True)[:50]}")
                    continue
                
                href = link_tag.get('href', '')
                if not href:
                    continue
                
                print(f"📝 제목 추출 성공: {title[:50]}...")
                
                # 링크 정리 및 post_id 추출
                if href.startswith('/zboard/'):
                    link = 'https://ppomppu.co.kr' + href
                else:
                    link = 'https://ppomppu.co.kr/zboard/' + href
                
                # post_id 추출 (중복 방지용 - 개선된 버전)
                post_id = None
                
                # 방법 1: URL에서 게시글 번호 추출
                if 'no=' in href:
                    post_id = href.split('no=')[-1].split('&')[0]
                elif 'view.php' in href and '/' in href:
                    post_id = href.split('/')[-1]
                
                # 방법 2: 제목과 링크 조합으로 고유 ID 생성 (더 안정적)
                if not post_id or not post_id.isdigit():
                    # 제목과 href를 조합한 해시 (더 정확한 중복 방지)
                    unique_string = f"{title.strip()}{href}"
                    post_id = str(abs(hash(unique_string)))[:12]
                
                print(f"🆔 생성된 post_id: {post_id} (href: {href[:50]}...)")
                print(f"📝 제목: {title[:50]}...")
                
                # 기본 중복 확인 (post_id와 제목 해시만)
                # 1차: post_id 기반 확인
                if post_id and is_post_already_sent(post_id):
                    print(f"🔄 [post_id] 이미 전송된 게시글 건너뛰기: {post_id}")
                    continue
                
                # 2차: 제목 해시 기반 확인  
                title_hash = str(abs(hash(title.strip())))[:10]
                if is_post_already_sent(f"title_{title_hash}"):
                    print(f"🔄 [title_hash] 동일 제목 게시글 건너뛰기: {title[:30]}...")
                    continue
                    
                # 3차: 링크 해시 기반 확인
                link_hash = str(abs(hash(link)))[:10]
                if is_post_already_sent(f"link_{link_hash}"):
                    print(f"🔄 [link_hash] 동일 링크 게시글 건너뛰기")
                    continue
                
                # 이미지 URL 추출
                img_tag = title_cell.select_one('img')
                image_url = None
                if img_tag and img_tag.get('src'):
                    img_src = img_tag['src']
                    if img_src.startswith('//'):
                        image_url = 'https:' + img_src
                    elif img_src.startswith('/'):
                        image_url = 'https://ppomppu.co.kr' + img_src
                    elif img_src.startswith('http'):
                        image_url = img_src
                
                # 모든 td 셀 가져오기
                all_tds = row.select('td')
                if len(all_tds) < 6:
                    continue
                
                # td 구조: [번호, 제목, 작성자, 시간, 추천, 조회수]
                post_time_str = all_tds[3].get_text(strip=True)
                vote_text = all_tds[4].get_text(strip=True)
                hits = int(all_tds[5].get_text(strip=True)) if all_tds[5].get_text(strip=True).isdigit() else 0
                
                # 추천수 파싱
                upvotes = 0
                if ' - ' in vote_text:
                    upvotes = int(vote_text.split(' - ')[0]) if vote_text.split(' - ')[0].isdigit() else 0
                
                # 시간 파싱
                try:
                    if ':' in post_time_str and len(post_time_str) <= 8:
                        if post_time_str.count(':') == 2:
                            post_time = datetime.strptime(post_time_str, '%H:%M:%S')
                        else:
                            post_time = datetime.strptime(post_time_str, '%H:%M')
                        post_time = post_time.replace(year=now.year, month=now.month, day=now.day)
                    else:
                        post_time = now
                except:
                    post_time = now
                
                # 제품명 추출 (뽐뿌 제목 형태 분석 - 개선된 버전)
                original_title = title
                product_name = title
                store_info = ""
                price_info = ""
                
                print(f"🔍 제목 분석: {title}")
                
                # 1. 상점명 추출 - 다양한 패턴 지원
                # [상점명], (상점명), 상점명: 형태
                store_patterns = [
                    r'^\[([^\]]+)\]',           # [11번가]
                    r'^\(([^)]+)\)',            # (쿠팡)
                    r'^([^:\[]+):\s*',          # 네이버:
                    r'([가-힣]+몰|[가-힣]+샵)',    # 옥션몰, G마켓
                ]
                
                for pattern in store_patterns:
                    store_match = re.search(pattern, title)
                    if store_match:
                        store_info = store_match.group(1).strip()
                        # 상점명 제거
                        title = title[len(store_match.group(0)):].strip()
                        break
                
                # 2. 가격 정보 추출 - 다양한 패턴
                price_patterns = [
                    r'\(([^)]*(?:\d+[,\d]*원|무료배송|무배|할인|원)[^)]*)\)',  # (19,900원/무배)
                    r'(\d+[,\d]*원)',                                      # 19,900원
                    r'(\d+[,\d]*\s*원)',                                   # 19,900 원
                    r'(무료배송|무배|할인)',                                  # 무료배송
                ]
                
                remaining_title = title
                for pattern in price_patterns:
                    price_match = re.search(pattern, remaining_title)
                    if price_match:
                        price_info = price_match.group(1).strip()
                        # 가격 정보 제거
                        remaining_title = remaining_title.replace(price_match.group(0), '').strip()
                        break
                
                # 3. 카테고리 제거
                category_patterns = [
                    r'\[[^\]]*\]$',             # 끝의 [카테고리]
                    r'\([^)]*\)$',              # 끝의 (카테고리)
                ]
                
                for pattern in category_patterns:
                    category_match = re.search(pattern, remaining_title)
                    if category_match:
                        remaining_title = remaining_title.replace(category_match.group(0), '').strip()
                
                # 4. 최종 정리
                product_name = remaining_title.strip()
                
                # 5. 기본값 설정
                if not store_info:
                    store_info = "기타"
                if not price_info:
                    price_info = "가격확인필요"
                if not product_name or len(product_name) < 3:
                    product_name = original_title[:50]  # 원본 제목 사용 (길이 제한)
                
                print(f"   ✅ 상점: {store_info}")
                print(f"   ✅ 가격: {price_info}")
                print(f"   ✅ 상품: {product_name[:40]}...")
                
                # 4차: 제목+상점 조합 중복 확인 (상점 정보 추출 후)
                title_store_combo = f"{original_title.strip()}_{store_info}".replace(" ", "")
                combo_hash = str(abs(hash(title_store_combo)))[:10]
                if is_post_already_sent(f"combo_{combo_hash}"):
                    print(f"🔄 [combo] 유사 상품 건너뛰기: {original_title[:20]}... @ {store_info}")
                    continue
                
                # 조건 확인: 최근 1시간 이내 + (추천≥3 and 조회≥1000) or (추천≥5)
                time_diff = now - post_time
                if time_diff <= timedelta(hours=1) and ((upvotes >= 3 and hits >= 1000) or upvotes >= 5):
                    new_posts.append((title, link, upvotes, hits, product_name, store_info, price_info, image_url, post_id))
                    print(f"📌 발견: {product_name[:30]}... (👍{upvotes}/👁{hits})")
                    
            except Exception as e:
                print(f"❗ 게시글 처리 오류: {e}")
                continue
        
        # 텔레그램 전송 (최대 3개로 제한)
        limited_posts = new_posts[:3]  # 최대 3개만 전송
        print(f"📤 전송할 게시글: {len(limited_posts)}개 (총 {len(new_posts)}개 발견)")
        
        for post in limited_posts:
            title, link, upvotes, hits, product_name, store_info, price_info, image_url, post_id = post
            
            # 안전한 값 설정
            safe_product_name = product_name.strip() if product_name and product_name.strip() else title[:50]
            safe_store_info = store_info.strip() if store_info and store_info.strip() else "기타"
            
            # 가격 정보가 의미있는 경우만 표시 (선택적 표시)
            has_meaningful_price = (
                price_info and 
                price_info.strip() and 
                price_info.strip() not in ["가격확인필요", "정보없음", "기타"] and
                ("원" in price_info or "무료" in price_info or "할인" in price_info or "무배" in price_info)
            )
            
            # 메시지 구성 - 클릭 가능한 링크 (disable_web_page_preview 강화)
            if has_meaningful_price:
                msg = f"""🔥 <b>뽐뿌 핫딜</b>

<b>🛍️ 상품:</b> {safe_product_name}
<b>🏪 상점:</b> {safe_store_info}
<b>💰 가격:</b> {price_info.strip()}

<b>📊 인기:</b> 👍 {upvotes} / 👁 {hits}

<a href="{link}">🔗 뽐뿌에서 보기</a>

<i>#{safe_store_info} #뽐뿌핫딜</i>"""
            else:
                msg = f"""🔥 <b>뽐뿌 핫딜</b>

<b>🛍️ 상품:</b> {safe_product_name}
<b>🏪 상점:</b> {safe_store_info}

<b>📊 인기:</b> 👍 {upvotes} / 👁 {hits}

<a href="{link}">🔗 뽐뿌에서 보기</a>

<i>#{safe_store_info} #뽐뿌핫딜</i>"""
            
            print(f"📤 전송:")
            print(f"   상품: {safe_product_name[:30]}...")
            print(f"   상점: {safe_store_info}")
            if has_meaningful_price:
                print(f"   가격: {price_info.strip()}")
            else:
                print(f"   가격: 정보없음 (숨김)")
            print(f"   인기: 👍{upvotes} 👁{hits}")
            
            # 텔레그램 전송 (disable_web_page_preview로 팝업 방지)
            success = send_telegram_message(msg, image_url)
            
            # 전송 성공시 모든 해시를 데이터베이스에 기록 (강화된 중복 방지)
            if success and post_id:
                # 1. post_id 저장
                save_sent_post(post_id, safe_product_name, link)
                
                # 2. 제목 해시 저장
                title_hash = str(abs(hash(title.strip())))[:10]
                save_sent_post(f"title_{title_hash}", safe_product_name, link)
                
                # 3. 링크 해시 저장
                link_hash = str(abs(hash(link)))[:10]
                save_sent_post(f"link_{link_hash}", safe_product_name, link)
                
                # 4. 제목+상점 조합 해시 저장
                title_store_combo = f"{title.strip()}_{safe_store_info}".replace(" ", "")
                combo_hash = str(abs(hash(title_store_combo)))[:10]
                save_sent_post(f"combo_{combo_hash}", safe_product_name, link)
                
                print(f"💾 중복 방지 기록 완료: post_id={post_id}, title_hash={title_hash}, link_hash={link_hash}, combo_hash={combo_hash}")
        
        if len(new_posts) == 0:
            print("📭 새로운 게시글이 없습니다.")
        
        return len(new_posts)
        
    except Exception as e:
        print(f"❌ 크롤링 오류: {e}")
        return 0

if __name__ == "__main__":
    result = crawl_ppomppu()
    print(f"🎯 완료: {result}개 게시글 처리됨")
