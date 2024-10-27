import base64
import re
from io import BytesIO
import pytesseract
from PIL import Image, ImageEnhance, ImageOps
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from transformers import pipeline

# NER 모델 로드 (약물 정보 추출용, 필요시 의료 데이터셋으로 학습 가능)
nlp = pipeline("ner", model="dslim/bert-base-NER")

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

            # 이미지 전처리: 그레이스케일 전환 및 대비 강화
            image = ImageOps.grayscale(image)
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2)  # 대비 강화

            # 한국어 OCR 수행 (언어 설정을 'kor'로)
            extracted_text = pytesseract.image_to_string(image, lang='kor+eng')

            # 약물 정보 및 투약량 추출 (정규 표현식 및 NER 모델 활용)
            medicine_pattern = r'\b([가-힣]+)\s+(\d+(?:mg|ml|정|캡슐))\b'
            matches = re.findall(medicine_pattern, extracted_text)

            medicines = [{'drug': match[0], 'dosage': match[1]} for match in matches]

            # 추가 NER 모델 사용 (옵션)
            entities = nlp(extracted_text)
            for entity in entities:
                if entity['entity'] == 'B-MISC':  # 약물 정보 필터링 예시
                    medicines.append({
                        'drug': entity['word'],
                        'start': entity['start'],
                        'end': entity['end']
                    })

            return JsonResponse({'text': extracted_text, 'medicines': medicines})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)
