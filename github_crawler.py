import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime, timedelta

# 환경변수에서 텔레그램 설정 가져오기
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def send_telegram_message(message):
    """텔레그램 메시지 전송"""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ 텔레그램 설정이 없습니다.")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        'chat_id': CHAT_ID,
        'text': message
    }
    
    try:
        response = requests.post(url, data=data, timeout=30)
        if response.status_code == 200:
            print("✅ 텔레그램 메시지 전송 성공")
            return True
        else:
            print(f"❌ 텔레그램 전송 실패: {response.status_code}")
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
                
                # 조건 확인: 최근 1시간 이내 + (추천≥3 and 조회≥1000) or (추천≥5)
                time_diff = now - post_time
                if time_diff <= timedelta(hours=1) and ((upvotes >= 3 and hits >= 1000) or upvotes >= 5):
                    new_posts.append((title, link, upvotes, hits))
                    print(f"📌 발견: {title[:50]}... (👍{upvotes}/👁{hits})")
                    
            except Exception as e:
                print(f"❗ 게시글 처리 오류: {e}")
                continue
        
        # 텔레그램 전송 (최대 3개로 제한)
        limited_posts = new_posts[:3]  # 최대 3개만 전송
        print(f"📤 전송할 게시글: {len(limited_posts)}개 (총 {len(new_posts)}개 발견)")
        
        for post in limited_posts:
            msg = f"🔥 [PPOMPPU 인기상품]\n{post[0]}\n👍 추천: {post[2]} / 👁 조회: {post[3]}\n🔗 {post[1]}"
            send_telegram_message(msg)
        
        if len(new_posts) == 0:
            print("📭 새로운 게시글이 없습니다.")
        
        return len(new_posts)
        
    except Exception as e:
        print(f"❌ 크롤링 오류: {e}")
        return 0

if __name__ == "__main__":
    result = crawl_ppomppu()
    print(f"🎯 완료: {result}개 게시글 처리됨")
