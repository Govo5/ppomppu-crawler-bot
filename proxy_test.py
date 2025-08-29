import requests
import urllib3

# SSL 경고 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_proxy_connection():
    """프록시 서버 연결 테스트"""
    print("🚀 프록시 서버 연결 테스트 시작\n")
    
    # 일반적인 프록시 포트들
    common_ports = ['8080', '3128', '1080', '8888', '9050', '7890', '10809']
    
    for port in common_ports:
        print(f"📡 127.0.0.1:{port} 테스트 중...")
        
        proxies = {
            'http': f'http://127.0.0.1:{port}',
            'https': f'http://127.0.0.1:{port}'
        }
        
        try:
            # 간단한 IP 확인 테스트
            response = requests.get(
                'https://httpbin.org/ip', 
                proxies=proxies, 
                timeout=5,
                verify=False
            )
            
            if response.status_code == 200:
                ip_info = response.json()
                print(f"✅ 포트 {port} 프록시 작동!")
                print(f"📍 프록시 IP: {ip_info.get('origin', 'unknown')}")
                
                # 텔레그램 테스트
                if test_telegram_via_proxy(proxies, port):
                    return port
                    
        except Exception as e:
            print(f"❌ 포트 {port} 실패: {str(e)[:50]}...")
    
    print("\n⚠️  활성화된 프록시를 찾을 수 없습니다.")
    return None

def test_telegram_via_proxy(proxies, port):
    """프록시를 통해 텔레그램 테스트"""
    TELEGRAM_TOKEN = '7250382833:AAGjJpqkln_zsISDO-AYrEmvNFmwmF98gZs'
    CHAT_ID = '59277305'
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    data = {
        'chat_id': CHAT_ID,
        'text': f'🎉 프록시 포트 {port}를 통한 텔레그램 연결 성공!'
    }
    
    try:
        print(f"🔍 포트 {port}로 텔레그램 API 테스트...")
        response = requests.post(
            url, 
            data=data, 
            proxies=proxies,
            timeout=10,
            verify=False
        )
        
        if response.status_code == 200:
            print(f"🎉 텔레그램 메시지 전송 성공! (포트 {port})")
            print(f"🎯 성공한 프록시 설정:")
            print(f"   PROXY_HOST=127.0.0.1")
            print(f"   PROXY_PORT={port}")
            return True
        else:
            print(f"❌ 텔레그램 실패 (포트 {port}, 상태코드: {response.status_code})")
            
    except Exception as e:
        print(f"❌ 텔레그램 테스트 실패 (포트 {port}): {str(e)[:50]}...")
    
    return False

def test_direct_connection():
    """프록시 없이 직접 연결 테스트"""
    print("\n🔍 프록시 없이 직접 연결 테스트...")
    
    TELEGRAM_TOKEN = '7250382833:AAGjJpqkln_zsISDO-AYrEmvNFmwmF98gZs'
    CHAT_ID = '59277305'
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    data = {
        'chat_id': CHAT_ID,
        'text': '🤖 직접 연결 테스트'
    }
    
    try:
        response = requests.post(
            url, 
            data=data, 
            timeout=10,
            verify=False
        )
        
        if response.status_code == 200:
            print("✅ 직접 연결 성공! 프록시가 필요 없습니다.")
            return True
        else:
            print(f"❌ 직접 연결 실패 (상태코드: {response.status_code})")
            
    except Exception as e:
        print(f"❌ 직접 연결 실패: {str(e)[:50]}...")
    
    return False

if __name__ == "__main__":
    # 먼저 직접 연결 시도
    if test_direct_connection():
        print("\n🎉 텔레그램이 직접 연결됩니다!")
        print("   프록시 설정이 필요 없습니다.")
    else:
        # 프록시 테스트
        working_port = test_proxy_connection()
        
        if working_port:
            print(f"\n🎯 성공! p_c.py의 기본값을 다음과 같이 설정하세요:")
            print(f"   PROXY_PORT = '{working_port}'")
        else:
            print("\n💡 해결 방안:")
            print("1. 프록시 서버가 실행 중인지 확인")
            print("2. 프록시 설정에서 포트 번호 확인")
            print("3. 프록시가 HTTPS를 지원하는지 확인")
            print("4. 다른 프록시 소프트웨어 사용 고려")

