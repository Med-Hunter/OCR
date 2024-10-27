import os
import json
import base64
import pytesseract
from PIL import Image, ImageEnhance, ImageOps
from io import BytesIO
import cv2
import re
import numpy as np
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from django.conf import settings

# 약물 데이터를 JSON 파일에서 로드
with open(os.path.join(settings.BASE_DIR, "ocr_app", "medicines.json"), "r", encoding="utf-8") as f:
    medicine_data = json.load(f)

@csrf_exempt
def ocr_prescription_base64(request):
    if request.method == 'POST':
        try:
            # 요청 바디에서 base64 이미지 데이터 받기
            data = request.POST.get('image_base64', None)
            if not data:
                return JsonResponse({'error': 'No image provided'}, status=400)

            # base64 문자열에서 이미지 디코딩
            image_data = base64.b64decode(data)
            image = Image.open(BytesIO(image_data))

            # 이미지 전처리
            processed_image = preprocess_image(image)

            # Tesseract OCR 설정
            custom_config = r'--oem 1 --psm 6'
            extracted_text = pytesseract.image_to_string(processed_image, config=custom_config, lang='kor+eng')

            # OCR 결과 텍스트 정제
            cleaned_text = clean_text(extracted_text)

            # 약물 이름 매칭
            medicines = match_medicines(cleaned_text)

            return JsonResponse({'text': cleaned_text, 'medicines': medicines})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)

def preprocess_image(image):
    # 이미지 전처리: 그레이스케일 변환, 대비 강화, 크기 조정, 이진화, 침식 및 팽창
    image = ImageOps.grayscale(image)
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2)
    new_size = (int(image.width * 1.5), int(image.height * 1.5))
    image = image.resize(new_size, Image.LANCZOS)

    # OpenCV로 이진화 및 노이즈 제거
    img_cv = np.array(image)
    _, img_bin = cv2.threshold(img_cv, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = np.ones((1, 1), np.uint8)
    img_bin = cv2.dilate(img_bin, kernel, iterations=1)
    img_bin = cv2.erode(img_bin, kernel, iterations=1)

    # 전처리된 이미지를 PIL 이미지로 변환
    processed_image = Image.fromarray(img_bin)
    return processed_image

def clean_text(text):
    # 텍스트 정제: 한글, 영문, 숫자, 공백 외의 문자 제거 및 다중 공백 축소
    text = re.sub(r'[^가-힣A-Za-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def match_medicines(text):
    matched_medicines = []

    # 정제된 텍스트에서 각 약물 이름과 매칭
    for medicine in medicine_data:
        match = process.extractOne(medicine["name"], text, scorer=fuzz.ratio)
        if match and match[1] > 75:  # 유사도가 75 이상일 때만 추가
            matched_medicines.append({
                'name': medicine['name'],
                'dosage': medicine['dosage'],
                'description': medicine['description'],
                'match_score': match[1]
            })

    return matched_medicines
