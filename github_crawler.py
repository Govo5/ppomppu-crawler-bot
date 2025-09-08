import requests
from bs4 import BeautifulSoup
import os
import re
from datetime import datetime, timedelta

# 환경변수에서 텔레그램 설정 가져오기
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

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
    
    URL = 'https://ppomppu.co.kr/zboard/zboard.php?id=ppomppu'
    
    try:
        response = requests.get(URL, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.select('tr.baseList')  # 수정된 셀렉터
        
        print(f"📊 찾은 게시글 수: {len(rows)}")
        
        new_posts = []
        now = datetime.now()
        
        for row in rows[:15]:  # 최신 15개만 확인
            try:
                # 제목과 링크 가져오기
                title_cell = row.select_one('td.title')
                if not title_cell:
                    continue
                
                
                link_tag = title_cell.select_one('a')
                if not link_tag:
                    continue
                    
                title = link_tag.get_text(strip=True)
                href = link_tag['href']
                
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
                
                # 제품명 추출 (실제 뽐뿌 제목 형태에 맞게 개선)
                original_title = title
                product_name = title
                store_info = "상점정보없음"
                price_info = "가격정보없음"
                
                print(f"🔍 제목 분석: {title}")
                
                # [상점명] 패턴 찾기 - 실제 형태: [11번가], [카카오], [네이버] 등
                store_match = re.search(r'^\[([^\]]+)\]', title)
                if store_match:
                    store_info = store_match.group(1)  # 대괄호 없이 상점명만
                    # 상점명 제거한 나머지가 상품명
                    remaining_title = title[len(store_match.group(0)):].strip()
                    product_name = remaining_title
                    print(f"   상점: {store_info}")
                    print(f"   남은제목: {remaining_title}")
                
                # 가격 정보 분리 - 실제 형태: (149,000원/무료), (19,900원/무배) 등
                price_match = re.search(r'\(([^)]*(?:\d+,?\d*원|무료|무배|할인)[^)]*)\)', product_name)
                if price_match:
                    price_info = price_match.group(1)
                    # 가격 정보 제거한 나머지가 순수 상품명
                    product_name = product_name.replace(price_match.group(0), '').strip()
                    print(f"   가격: {price_info}")
                    print(f"   상품명: {product_name}")
                
                # 카테고리 정보 제거 - [기타], [식품/건강] 등
                category_match = re.search(r'\[[^\]]*\]$', product_name)
                if category_match:
                    product_name = product_name.replace(category_match.group(0), '').strip()
                    print(f"   카테고리 제거 후: {product_name}")
                
                # 최종 검증 및 기본값 설정
                if not product_name or len(product_name.strip()) < 3:
                    product_name = original_title
                    store_info = "상점정보없음"
                    price_info = "가격정보없음"
                    print(f"   ⚠️ 파싱 실패, 원본 사용: {product_name}")
                
                print(f"   ✅ 최종 - 상점:{store_info} / 가격:{price_info} / 상품:{product_name[:30]}...")
                
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
            
            # 값이 비어있거나 None인 경우 기본값 설정
            safe_product_name = product_name if product_name and product_name.strip() else "상품명 정보없음"
            safe_store_info = store_info if store_info and store_info.strip() else "상점 정보없음"  
            safe_price_info = price_info if price_info and price_info.strip() else "가격 정보없음"
            
            # HTML 형식으로 메시지 구성
            msg = f"""🔥 <b>뽐뿌 인기상품</b>

<b>🏷️ 상품명:</b> {safe_product_name}
<b>🏪 상점:</b> {safe_store_info}
<b>💰 가격:</b> {safe_price_info}

<b>📊 인기도:</b> 👍 {upvotes} / 👁 {hits}

<a href="{link}">🔗 상품 보러가기</a>"""
            
            print(f"📤 전송 내용 미리보기:")
            print(f"   상품명: {safe_product_name}")
            print(f"   상점: {safe_store_info}")
            print(f"   가격: {safe_price_info}")
            
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
