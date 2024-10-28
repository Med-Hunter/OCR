import pytesseract
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import base64
import re
from io import BytesIO
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def ocr_prescription_base64(request):
    if request.method == 'POST':
        try:
            # 요청 바디에서 base64 이미지 데이터 받기
            data = request.POST.get('image_base64', None)
            if not data:
                return JsonResponse({'error': 'No image provided'}, status=400)

            # Base64 문자열에서 이미지 디코딩
            image_data = base64.b64decode(data)
            image = Image.open(BytesIO(image_data)).convert("RGB")
            image = preprocess_image(image)  # 이미지 전처리

            # Tesseract OCR을 사용해 텍스트 추출 (한글+영어, 설정 추가)
            text = pytesseract.image_to_string(image, lang='kor+eng', config='--oem 1 --psm 6')

            # 텍스트 정제
            cleaned_text = clean_text(text)

            # 약물 정보 추출
            medicines = extract_medicines_from_text(cleaned_text)

            return JsonResponse({'text': cleaned_text, 'medicines': medicines})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)

def preprocess_image(image):
    image = ImageOps.grayscale(image)
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2)
    new_size = (int(image.width * 1.5), int(image.height * 1.5))
    image = image.resize(new_size, Image.LANCZOS)
    image = image.filter(ImageFilter.MedianFilter(size=3))
    image = image.convert("RGB")
    return image

def clean_text(text):
    text = re.sub(r'[^가-힣A-Za-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()

    # 약물명과 숫자 사이에 띄어쓰기 추가
    text = re.sub(r'(?<=\d)(?=[가-힣A-Za-z])', ' ', text)
    text = re.sub(r'(?<=[가-힣])(?=\d)', ' ', text)
    return text

def extract_medicines_from_text(text):
    medicine_pattern = r'([가-힣A-Za-z]+(?:캡셀|정|액|주사제|산|수용액)?)\s*(\d+(?:mg|ml|정|캡슐|회|일)?)'
    matches = re.findall(medicine_pattern, text)
    medicines = [{'drug': match[0], 'dosage': match[1] if match[1] else 'N/A'} for match in matches]
    return medicines
