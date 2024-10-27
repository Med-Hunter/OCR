from django.urls import path
from .views import ocr_prescription_base64

urlpatterns = [
    path('ocr_base64/', ocr_prescription_base64, name='ocr_prescription_base64'),
]
