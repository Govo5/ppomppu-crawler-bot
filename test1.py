import requests
from bs4 import BeautifulSoup
import time
import datetime
import re

import schedule
import time
from datetime import datetime, timedelta


# ▶️ 텔레그램 설정

TELEGRAM_TOKEN = '7250382833:AAGjJpqkln_zsISDO-AYrEmvNFmwmF98gZs'
CHAT_ID = '59277305'

# ▶️ 크롤링 함수
def crawl_ppomppu():
    url = 'https://www.ppomppu.co.kr/zboard/zboard.php?id=ppomppu'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # td 단위로 셀렉터 변경
    tds = soup.select('td.baseList-space.title')

    print(f"가져온 글 수: {len(tds)}")
    posts = []

    for td in tds:
        # 제목 및 링크 추출
        subject_tag = td.select_one('a.baseList-title')
        if not subject_tag:
            continue    
        
        title = subject_tag.text.strip()
        link = 'https://www.ppomppu.co.kr/zboard/' + subject_tag['href']

        # 추천수 가져오기: 부모의 형제 요소에서 찾아야 할 가능성 큼
        rec_tag = td.find_next_sibling('td', class_='baseList-space baseList-rec')
        recommend_text = rec_tag.text.strip() if rec_tag else '0-0'

        if '-' in recommend_text:
            recommend_part = recommend_text.split('-')[0].strip()
        else:
            recommend_part = recommend_text.strip()

        # recommend_part가 숫자인지 확인 후 int로 변환, 아니면 0
        recommend = int(recommend_part) if recommend_part.isdigit() else 0

        # 조회수 가져오기
        view_tag = td.find_next_sibling('td', class_='baseList-space baseList-views')
        view_count = int(view_tag.text.strip().replace(',', '')) if view_tag else 0
        
        # 작성 시간 가져오기
        time_element = td.find_next('time', class_='baseList-time')
        time_text = time_element.text.strip() if time_element else None

        # 시간 비교 로직 (최근 15분 이내)
        is_recent = False
        time_diff = None
        # print(time_text)
        if time_text:
            # 시간 형식이 아닌 경우 걸러내기 (예: '25/05/14' 같은 날짜 형식)
            if not re.match(r'^\d{2}:\d{2}:\d{2}$', time_text):
                #print(f"시간 형식 아님, 스킵: {time_text}")
                continue
            try:
                # 작성 시각을 오늘 날짜로 만들어 datetime 객체 생성
                now = datetime.now()
                post_time = datetime.strptime(time_text, '%H:%M:%S')
                post_datetime = now.replace(hour=post_time.hour, minute=post_time.minute, second=0, microsecond=0)

                # 만약 작성 시간이 현재보다 미래라면 어제 글일 수 있으므로 하루 빼줌 (자정 넘어가는 케이스)
                if post_datetime > now:
                    post_datetime -= datetime.timedelta(days=1)

                # 현재 시각과의 차이 계산
                time_diff = now - post_datetime
                if time_diff.total_seconds() <= 15 * 60:
                    is_recent = True
            except Exception as e:
                print(f"시간 파싱 실패: {time_text}, 오류: {e}")
                continue  
        else:  
            continue

        #print(f"time:{time_text} 차이 : {time_diff}") 

        # 조건: 최근 15분 이내 + 추천 1 이상 또는 조회수 500 이상
        if is_recent and (recommend >= 1 or view_count >= 300):
            #print("govo")
            print(f"[추천: {recommend} / 조회수: {view_count} / 작성시간: {time_text}] {title} ({link}) {time_diff}")
            posts.append((title, link, recommend, view_count))
            
        return posts
        #print(f"[추천: {recommend} / 조회수: {view_count} / 작성시간: {time_text}] {title} ({link}) {time_diff}")

def job():
    now = datetime.now()
    current_hour = now.hour

    # 0시~7시는 스킵
    if 0 <= current_hour < 8:
        print(f"[{now.strftime('%H:%M:%S')}] ❌ 스케줄 제외 시간대입니다.")
        return

    print(f"[{now.strftime('%H:%M:%S')}] ✅ 크롤링 실행 중...")

    posts = crawl_ppomppu()
    if posts:
        for title, link, rec, view in posts:
            msg = f'📢 <b>{title}</b>\n추천: {rec} | 조회: {view}\n🔗 {link}'
            print(f'보내는 중: {title}')
            send_telegram(msg)
    else:
        print('조건을 만족하는 게시물이 없습니다.')

# ⏰ 매 5분마다 실행
schedule.every(5).minutes.do(job)

print("🕒 스케줄러 시작됨 (5분마다 실행, 08시~23시 동작)")

while True:
    schedule.run_pending()
    time.sleep(1)


# ▶️ 텔레그램 알림 함수
def send_telegram(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    data = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    requests.post(url, data=data)

# ▶️ 메인 실행
if __name__ == '__main__':
    posts = crawl_ppomppu()
    if posts:
        for title, link, rec, view in posts:
            msg = f'📢 <b>{title}</b>\n추천: {rec} | 조회: {view}\n🔗 {link}'
            print(f'보내는 중: {title}')
            send_telegram(msg)
    else:
        print('조건을 만족하는 게시물이 없습니다.')

