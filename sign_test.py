import time, hmac, hashlib, base64

API_KEY = "0100000000cbd1b42f3b10f4cee16e8ad46e0bb16dce493fbb953b7bed4fe832ad5682998c"
SECRET_KEY = "AQAAAACJxp/PlQhwCIF35Ar48Fob9ez5A+f3F26dg9pHEs2r5A=="
CUSTOMER_ID = "3430619"
METHOD = "POST"
URI = "/keywordstool"

timestamp = str(int(time.time() * 1000))
message = f"{timestamp}.{METHOD}.{URI}"
signature = base64.b64encode(hmac.new(
    SECRET_KEY.encode(),
    message.encode(),
    hashlib.sha256
).digest()).decode()

print("X-Timestamp:", timestamp)
print("X-Signature:", signature)