import requests
from bs4 import BeautifulSoup
import os
import re
from datetime import datetime, timedelta

# 환경변수에서 텔레그램 설정 가져오기 (테스트용 기본값 포함)
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN') or '7250382833:AAGjJpqkln_zsISDO-AYrEmvNFmwmF98gZs'
CHAT_ID = os.getenv('CHAT_ID') or '59277305'

def send_telegram_message(message, image_url=None):
    """텔레그램 메시지 전송 (이미지 포함 가능)"""
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
                'parse_mode': 'HTML'
            }
        else:
            # 텍스트만 전송
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            data = {
                'chat_id': CHAT_ID,
                'text': message,
                'parse_mode': 'HTML'
            }
        
        response = requests.post(url, data=data, timeout=30)
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
                
                # 링크 중복 제거
                if href.startswith('/zboard/'):
                    link = 'https://ppomppu.co.kr' + href
                else:
                    link = 'https://ppomppu.co.kr/zboard/' + href
                
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
                
                # 조건 확인: 최근 1시간 이내 + (추천≥3 and 조회≥1000) or (추천≥5)
                time_diff = now - post_time
                if time_diff <= timedelta(hours=1) and ((upvotes >= 3 and hits >= 1000) or upvotes >= 5):
                    new_posts.append((title, link, upvotes, hits, product_name, store_info, price_info, image_url))
                    print(f"📌 발견: {product_name[:30]}... (👍{upvotes}/👁{hits})")
                    
            except Exception as e:
                print(f"❗ 게시글 처리 오류: {e}")
                continue
        
        # 텔레그램 전송 (최대 3개로 제한)
        limited_posts = new_posts[:3]  # 최대 3개만 전송
        print(f"📤 전송할 게시글: {len(limited_posts)}개 (총 {len(new_posts)}개 발견)")
        
        for post in limited_posts:
            title, link, upvotes, hits, product_name, store_info, price_info, image_url = post
            
            # 안전한 값 설정 (더 의미있는 기본값)
            safe_product_name = product_name.strip() if product_name and product_name.strip() else title[:50]
            safe_store_info = store_info.strip() if store_info and store_info.strip() else "기타"
            safe_price_info = price_info.strip() if price_info and price_info.strip() else "가격확인필요"
            
            # HTML 형식으로 메시지 구성 (더 간결하고 명확하게)
            msg = f"""🔥 <b>뽐뿌 핫딜</b>

<b>🛍️ 상품:</b> {safe_product_name}
<b>🏪 상점:</b> {safe_store_info}
<b>💰 가격:</b> {safe_price_info}

<b>📊 인기:</b> 👍 {upvotes} / 👁 {hits}

<a href="{link}">🔗 바로가기</a>

<i>#{safe_store_info} #뽐뿌핫딜</i>"""
            
            print(f"📤 전송:")
            print(f"   상품: {safe_product_name[:30]}...")
            print(f"   상점: {safe_store_info}")
            print(f"   가격: {safe_price_info}")
            print(f"   인기: 👍{upvotes} 👁{hits}")
            
            send_telegram_message(msg, image_url)
        
        if len(new_posts) == 0:
            print("📭 새로운 게시글이 없습니다.")
        
        return len(new_posts)
        
    except Exception as e:
        print(f"❌ 크롤링 오류: {e}")
        return 0

if __name__ == "__main__":
    result = crawl_ppomppu()
    print(f"🎯 완료: {result}개 게시글 처리됨")
