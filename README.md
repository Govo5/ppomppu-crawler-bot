# 뽐뿌 크롤링 봇 🤖

GitHub Actions를 사용해서 뽐뿌 할인정보를 자동으로 크롤링하고 텔레그램으로 알림을 보내는 봇입니다.

## 🚀 설정 방법

### 1. GitHub Secrets 설정
Repository Settings → Secrets and variables → Actions에서 다음 값들을 추가하세요:

- `TELEGRAM_TOKEN`: 텔레그램 봇 토큰
- `CHAT_ID`: 텔레그램 채팅 ID

### 2. 자동 실행
- **15분마다 자동 실행**됩니다
- 수동 실행: Actions 탭에서 "Run workflow" 버튼 클릭

### 3. 알림 조건
- 최근 1시간 이내 게시글
- 추천 1개 이상 OR 조회수 500회 이상

## 📁 파일 구조
- `github_crawler.py`: GitHub Actions용 크롤링 스크립트
- `p_c.py`: 로컬 실행용 스크립트
- `.github/workflows/ppomppu-bot.yml`: GitHub Actions 워크플로우

## 🔧 로컬 테스트
```bash
python github_crawler.py
```

## 📊 모니터링
GitHub Actions 탭에서 실행 로그를 확인할 수 있습니다.
