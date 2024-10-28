from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from transformers import DonutProcessor, VisionEncoderDecoderModel
from PIL import Image
import base64
from io import BytesIO
import re

# Donut 모델과 프로세서 초기화
processor = DonutProcessor.from_pretrained("naver-clova-ix/donut-base")
model = VisionEncoderDecoderModel.from_pretrained("naver-clova-ix/donut-base")

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

            # Donut 모델을 사용해 텍스트 추출
            pixel_values = processor(image, return_tensors="pt").pixel_values
            outputs = model.generate(pixel_values, max_new_tokens=200, num_beams=5)
            text = processor.batch_decode(outputs, skip_special_tokens=True)[0]

            # 텍스트 정제 및 약물 정보 추출
            cleaned_text = clean_text(text)
            medicines = extract_medicines_from_text(cleaned_text)

            return JsonResponse({'text': cleaned_text, 'medicines': medicines})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)

def clean_text(text):
    # Donut이 반환한 텍스트에서 불필요한 공백과 특수 문자 제거
    text = re.sub(r'[^가-힣A-Za-z0-9\s]', '', text)  # 한글, 영문, 숫자, 공백만 남김
    text = re.sub(r'\s+', ' ', text)  # 다중 공백을 단일 공백으로 변환
    return text.strip()

def extract_medicines_from_text(text):
    # 약물명과 용량 추출을 위한 정규 표현식
    medicine_pattern = r'([가-힣A-Za-z]+(?:캡셀|정|액|주사제|산|수용액)?)\s*(\d+(?:mg|ml|정|캡슐|회|일|분|C)?)'
    matches = re.findall(medicine_pattern, text)

    # 불필요한 약물명 제거
    valid_medicines = []
    for match in matches:
        drug, dosage = match
        # 불필요한 단어 필터링 (예: "씩", "실온" 등)
        if drug not in ['씩', '실온', '회', '분']:
            valid_medicines.append({'drug': drug, 'dosage': dosage if dosage else 'N/A'})

    return valid_medicines
