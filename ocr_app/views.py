import pytesseract
from PIL import Image
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
import os

@csrf_exempt
def ocr_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        # 업로드된 파일 가져오기
        uploaded_file = request.FILES['image']
        file_name = default_storage.save(uploaded_file.name, uploaded_file)
        file_path = os.path.join(default_storage.location, file_name)

        # 이미지 열기 및 OCR 수행
        try:
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img, lang='kor')  # 한국어 OCR
            return JsonResponse({'text': text})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        finally:
            # 파일 삭제
            default_storage.delete(file_name)
    return JsonResponse({'error': 'Invalid request'}, status=400)
