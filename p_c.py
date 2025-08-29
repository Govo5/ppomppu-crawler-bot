import requests
from bs4 import BeautifulSoup
import sqlite3
import time
from datetime import datetime, timedelta
import telegram
from apscheduler.schedulers.blocking import BlockingScheduler

# ▶️ 환경 설정
DB_PATH = 'ppomppu_crawl.db'
URL = 'https://ppomppu.co.kr/zboard/zboard.php?id=ppomppu'
TELEGRAM_TOKEN = '7250382833:AAGjJpqkln_zsISDO-AYrEmvNFmwmF98gZs'
CHAT_ID = '59277305'

# 프록시 설정 (프록시 포트를 아시면 여기에 입력)
PROXY_PORT = None  # 예: 7890, 10809, 1080 등

# ▶️ 텔레그램 봇 초기화
bot = telegram.Bot(token=TELEGRAM_TOKEN)

# ▶️ SQLite 초기화
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            title TEXT,
            link TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# ▶️ 크롤링 함수
def crawl():
    print("✅ 크롤링 시작:", datetime.now())
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    rows = soup.select('tr.line')  # 각 게시글 라인

    new_posts = []

    for row in rows:
        try:
            title_tag = row.select_one('font.list_title')
            if not title_tag:
                continue

            link_tag = title_tag.parent
            title = title_tag.get_text(strip=True)
            link = 'https://ppomppu.co.kr' + link_tag['href']
            post_id = link.split('no=')[-1]

            # 추천수, 조회수 가져오기
            upvote_tag = row.select_one('td.eng.list_vspace')
            upvotes = int(upvote_tag.get_text(strip=True)) if upvote_tag else 0

            hits_tag = row.select('td.eng.list_vspace')[-1]
            hits = int(hits_tag.get_text(strip=True)) if hits_tag else 0

            # 작성시간 확인
            date_tag = row.select_one('td.eng.list_vspace')
            post_time_str = date_tag.get_text(strip=True)

            # 포럼은 시간만 나오는 구조(오늘 날짜로 가정)
            now = datetime.now()
            post_time = datetime.strptime(post_time_str, '%H:%M')
            post_time = post_time.replace(year=now.year, month=now.month, day=now.day)

            # 최근 15분 이내 게시글 필터링 + 추천≥1 or 조회≥500
            if (now - post_time <= timedelta(minutes=15)) and (upvotes >= 1 or hits >= 500):
                # DB에 있는지 확인
                if not check_post_exists(post_id):
                    save_post(post_id, title, link)
                    new_posts.append((title, link, upvotes, hits))
        except Exception as e:
            print("❗ 오류:", e)

    # ▶️ 텔레그램 발송
    for post in new_posts:
        msg = f"🔥 [PPOMPPU]\n{post[0]}\n👍 추천: {post[2]} / 👁 조회: {post[3]}\n🔗 {post[1]}"
        bot.send_message(chat_id=CHAT_ID, text=msg)

# ▶️ DB 저장 및 중복 확인
def save_post(post_id, title, link):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO posts (id, title, link) VALUES (?, ?, ?)', (post_id, title, link))
    conn.commit()
    conn.close()

def check_post_exists(post_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT 1 FROM posts WHERE id = ?', (post_id,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

# ▶️ 스케줄러 설정
if __name__ == '__main__':
    init_db()
    scheduler = BlockingScheduler()
    scheduler.add_job(crawl, 'interval', minutes=15)
    print("⏳ 15분 간격으로 크롤링 시작!")
    scheduler.start()
