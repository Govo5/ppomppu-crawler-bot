
import requests
import time
import hmac
import hashlib
import base64
import json

# ▶️ 환경 설정
API_BASE_URL = "https://api.searchad.naver.com"
API_KEY = "0100000000cbd1b42f3b10f4cee16e8ad46e0bb16dce493fbb953b7bed4fe832ad5682998c"
SECRET_KEY = "AQAAAACJxp/PlQhwCIF35Ar48Fob9ez5A+f3F26dg9pHEs2r5A=="
CUSTOMER_ID = "3430619"  # 숫자만

def generate_signature(timestamp, method, uri):
    message = f"{timestamp}.{method}.{uri}"
    signature = hmac.new(
        bytes(SECRET_KEY, 'utf-8'),
        bytes(message, 'utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(signature).decode()

def get_headers(uri, method):
    timestamp = str(int(time.time() * 1000))
    signature = generate_signature(timestamp, method, uri)
    return {
        "Content-Type": "application/json; charset=UTF-8",
        "X-Timestamp": timestamp,
        "X-API-KEY": API_KEY,
        "X-Customer": CUSTOMER_ID,
        "X-Signature": signature
    }

def get_keyword_info(keyword):
    uri = "/keywordstool"
    # uri = "/customer-links"
    url = API_BASE_URL + uri
    method = "POST"
    headers = get_headers(uri, method)

    payload = {
        "hintKeywords": [keyword],
        "showDetail": 1
    }

    response = requests.post(url, headers=headers, json=payload)

   # print("응답 코드:", response.status_code)
   # print("사용한 CUSTOMER_ID:", CUSTOMER_ID)
   # print("사용한 API_KEY:", API_KEY[:5] + "****")
   # print("사용한 키워드:", keyword)
    if response.status_code == 200:
        data = response.json()
        print("data:", data)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print("❌ API 호출 실패:", response.text)

# ▶️ 실행
get_keyword_info("송월타월")
