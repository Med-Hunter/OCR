import base64
from io import BytesIO
import pytesseract
from PIL import Image
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from transformers import pipeline
import re

# NER 모델 로드
nlp = pipeline("ner", model="dslim/bert-base-NER")

@csrf_exempt
def ocr_prescription_base64(request):
    if request.method == 'POST':
        try:
            # 요청의 바디에서 base64 이미지 데이터 받기
            data = request.POST.get('image_base64', None)
            if not data:
                return JsonResponse({'error': 'No image provided'}, status=400)

            # base64 문자열에서 이미지 디코딩
            image_data = base64.b64decode(data)
            image = Image.open(BytesIO(image_data))

            # OCR 수행
            extracted_text = pytesseract.image_to_string(image, lang='eng')

            # 약물 정보 및 투약량 추출
            entities = nlp(extracted_text)

            medicines = []
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
