
import time
import requests

import signaturehelper

def get_header(method, uri, api_key, secret_key, customer_id):
    timestamp = str(round(time.time() * 1000))
    signature = signaturehelper.Signature.generate(timestamp, method, uri, SECRET_KEY)
    return {'Content-Type': 'application/json; charset=UTF-8', 'X-Timestamp': timestamp, 'X-API-KEY': API_KEY, 'X-Customer': str(CUSTOMER_ID), 'X-Signature': signature}
    #return {'Content-Type': 'application/json; charset=UTF-8', 'X-Timestamp': timestamp, 'X-API-KEY': API_KEY, 'X-Customer': str(CUSTOMER_ID), 'X-Signature': signature}


BASE_URL = 'https://api.searchad.naver.com'
API_KEY = '0100000000a4e519b350f2865ac0d0e9e1b3d86c20ccc7e64cecce1309f4be79b8c52918de'
SECRET_KEY = 'AQAAAACk5RmzUPKGWsDQ6eGz2GwgUy+HqETjgCQziH8qk531uA=='
CUSTOMER_ID = '3430619' #'CUSTOMER_ID' #'hellomeet77@naver.com'

#Sample 
uri = '/keywordstool'
method = 'GET'
response = requests.get(BASE_URL + uri + '?hintKeywords=네이버광고&showDetail=1', headers=get_header(method, uri, API_KEY, SECRET_KEY, CUSTOMER_ID))

print(response.json()['keywordList'][0])