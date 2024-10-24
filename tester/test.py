import base64
import requests

# 이미지 파일을 base64로 인코딩
with open("prescription.png", "rb") as image_file:
    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

# API 요청
url = 'http://127.0.0.1:8000/ocr_base64/'
data = {
    'image_base64': encoded_string
}
response = requests.post(url, data=data)

# 결과 출력
print(response.json())
